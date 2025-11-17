"""
Flask API for M5 Clipping Service.

Implements 6 RESTful endpoints for video clipping service:
1. POST /v1/clip/request - Submit clipping request
2. GET /v1/clip/{request_id}/status - Check status
3. GET /v1/clip/{request_id}/download - Get download URL
4. GET /v1/admin/agents - Agent status
5. GET /v1/stats - Clipping statistics
6. GET /health - Health check
"""

import logging
import re
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException

from app.config import get_config
from app.status_tracker import get_tracker
from app.pubsub_publisher import get_publisher
from app.gcs_client import get_gcs_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Initialize services
tracker = get_tracker()
publisher = get_publisher()
gcs_client = get_gcs_client()


def generate_request_id() -> str:
    """Generate unique request ID: clip-YYYYMMDD-NNN"""
    date_str = datetime.utcnow().strftime('%Y%m%d')

    # Get count of requests today
    all_requests = tracker.get_all_requests()
    today_requests = [
        r for r in all_requests
        if r.request_id.startswith(f'clip-{date_str}')
    ]

    sequence = len(today_requests) + 1
    return f"clip-{date_str}-{sequence:03d}"


def validate_request_id(request_id: str) -> bool:
    """Validate request ID format."""
    pattern = r'^clip-\d{8}-\d{3}$'
    return bool(re.match(pattern, request_id))


@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler."""
    if isinstance(error, HTTPException):
        response = {
            'error': {
                'code': error.name,
                'message': error.description
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        return jsonify(response), error.code

    logger.error(f"Unhandled error: {error}", exc_info=True)
    response = {
        'error': {
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'An unexpected error occurred'
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    return jsonify(response), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns service status and agent availability.
    """
    queue_depth = tracker.get_queue_depth()

    # In production, would check actual agent status via Pub/Sub
    # For now, mock agent status based on environment
    agents_status = {
        'primary': 'active' if not config.is_development() else 'active',
        'standby': 'standby' if not config.is_development() else 'down'
    }

    # Determine overall health
    status = 'healthy'
    if agents_status['primary'] == 'down':
        status = 'degraded'

    return jsonify({
        'status': status,
        'api_status': 'ok',
        'agents': agents_status,
        'queue_depth': queue_depth,
        'environment': config.ENV,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@app.route('/v1/clip/request', methods=['POST'])
def request_clip():
    """
    Submit a clipping request.

    Request body:
        {
            "hand_id": "wsop2024_me_d3_h154",
            "nas_video_path": "/nas/poker/2024/wsop/main_event_day3.mp4",
            "start_seconds": 12255,
            "end_seconds": 12405,
            "output_quality": "high"  // optional, default "high"
        }

    Response:
        {
            "request_id": "clip-20241117-001",
            "hand_id": "wsop2024_me_d3_h154",
            "status": "queued",
            "estimated_duration_sec": 45,
            "queue_position": 3,
            "created_at": "2024-11-17T14:00:00Z"
        }
    """
    data = request.get_json()

    # Validate required fields
    required_fields = ['hand_id', 'nas_video_path', 'start_seconds', 'end_seconds']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': f'Missing required field: {field}'
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400

    # Validate time range
    if data['start_seconds'] >= data['end_seconds']:
        return jsonify({
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'start_seconds must be less than end_seconds'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 400

    # Validate clip duration (max 10 minutes)
    duration = data['end_seconds'] - data['start_seconds']
    if duration > 600:
        return jsonify({
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Clip duration exceeds maximum of 10 minutes'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 400

    output_quality = data.get('output_quality', 'high')
    if output_quality not in ['high', 'medium']:
        return jsonify({
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'output_quality must be "high" or "medium"'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 400

    try:
        # Generate request ID
        request_id = generate_request_id()

        # Create request in tracker
        clip_request = tracker.create_request(
            request_id=request_id,
            hand_id=data['hand_id'],
            nas_video_path=data['nas_video_path'],
            start_seconds=data['start_seconds'],
            end_seconds=data['end_seconds'],
            output_quality=output_quality
        )

        # Publish to Pub/Sub
        publisher.publish_clipping_request(
            request_id=request_id,
            hand_id=data['hand_id'],
            nas_video_path=data['nas_video_path'],
            start_seconds=data['start_seconds'],
            end_seconds=data['end_seconds'],
            output_quality=output_quality
        )

        logger.info(f"Clipping request created: {request_id}")

        return jsonify({
            'request_id': clip_request.request_id,
            'hand_id': clip_request.hand_id,
            'status': clip_request.status,
            'estimated_duration_sec': clip_request.estimated_duration_sec,
            'queue_position': clip_request.queue_position,
            'created_at': clip_request.created_at
        }), 200

    except Exception as e:
        logger.error(f"Failed to create clipping request: {e}")
        return jsonify({
            'error': {
                'code': 'REQUEST_FAILED',
                'message': str(e)
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@app.route('/v1/clip/<request_id>/status', methods=['GET'])
def get_clip_status(request_id: str):
    """
    Get clipping request status.

    Response:
        {
            "request_id": "clip-20241117-001",
            "hand_id": "wsop2024_me_d3_h154",
            "status": "completed",  // queued, processing, completed, failed
            "output_gcs_path": "gs://gg-subclips/wsop2024_me_d3_h154.mp4",
            "download_url": "https://storage.googleapis.com/...",
            "file_size_bytes": 52428800,
            "duration_seconds": 150,
            "processing_time_seconds": 45,
            "download_url_expires_at": "2024-11-17T15:00:00Z",
            "completed_at": "2024-11-17T14:01:00Z"
        }
    """
    if not validate_request_id(request_id):
        return jsonify({
            'error': {
                'code': 'INVALID_REQUEST_ID',
                'message': 'Invalid request_id format'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 400

    clip_request = tracker.get_request(request_id)

    if not clip_request:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Request not found: {request_id}'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 404

    return jsonify(clip_request.to_dict()), 200


@app.route('/v1/clip/<request_id>/download', methods=['GET'])
def get_download_url(request_id: str):
    """
    Get signed download URL for completed clip.

    Response:
        {
            "request_id": "clip-20241117-001",
            "hand_id": "wsop2024_me_d3_h154",
            "download_url": "https://storage.googleapis.com/...",
            "expires_at": "2024-11-24T14:00:00Z",
            "file_size_bytes": 52428800
        }
    """
    if not validate_request_id(request_id):
        return jsonify({
            'error': {
                'code': 'INVALID_REQUEST_ID',
                'message': 'Invalid request_id format'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 400

    clip_request = tracker.get_request(request_id)

    if not clip_request:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Request not found: {request_id}'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 404

    if clip_request.status != 'completed':
        return jsonify({
            'error': {
                'code': 'NOT_READY',
                'message': f'Clip is not ready for download. Current status: {clip_request.status}'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 400

    try:
        # Generate signed URL
        download_url, expires_at = gcs_client.generate_signed_url(clip_request.hand_id)

        # Update request with new download URL
        tracker.update_status(
            request_id,
            status='completed',
            download_url=download_url,
            download_url_expires_at=expires_at
        )

        return jsonify({
            'request_id': request_id,
            'hand_id': clip_request.hand_id,
            'download_url': download_url,
            'expires_at': expires_at,
            'file_size_bytes': clip_request.file_size_bytes
        }), 200

    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        return jsonify({
            'error': {
                'code': 'URL_GENERATION_FAILED',
                'message': str(e)
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@app.route('/v1/admin/agents', methods=['GET'])
def get_agent_status():
    """
    Get status of all clipping agents.

    Response:
        {
            "agents": [
                {
                    "agent_id": "nas-server-01",
                    "role": "primary",
                    "status": "active",
                    "last_heartbeat": "2024-11-17T14:00:00Z",
                    "queue_depth": 3,
                    "completed_clips_24h": 450
                },
                {
                    "agent_id": "nas-server-02",
                    "role": "standby",
                    "status": "standby",
                    "last_heartbeat": "2024-11-17T14:00:05Z",
                    "queue_depth": 0,
                    "completed_clips_24h": 0
                }
            ]
        }
    """
    # In production, this would query agent heartbeat from Pub/Sub or database
    # For now, return mock data based on environment

    if config.is_development():
        agents = [
            {
                'agent_id': 'local-dev-agent',
                'role': 'primary',
                'status': 'active',
                'last_heartbeat': datetime.utcnow().isoformat() + 'Z',
                'queue_depth': tracker.get_queue_depth(),
                'completed_clips_24h': len(tracker.get_requests_by_status('completed'))
            }
        ]
    else:
        agents = [
            {
                'agent_id': 'nas-server-01',
                'role': 'primary',
                'status': 'active',
                'last_heartbeat': datetime.utcnow().isoformat() + 'Z',
                'queue_depth': tracker.get_queue_depth(),
                'completed_clips_24h': 450
            },
            {
                'agent_id': 'nas-server-02',
                'role': 'standby',
                'status': 'standby',
                'last_heartbeat': datetime.utcnow().isoformat() + 'Z',
                'queue_depth': 0,
                'completed_clips_24h': 0
            }
        ]

    return jsonify({'agents': agents}), 200


@app.route('/v1/stats', methods=['GET'])
def get_stats():
    """
    Get clipping statistics.

    Query parameters:
        period: 24h, 7d, 30d (default: 24h)

    Response:
        {
            "period": "24h",
            "total_requests": 580,
            "completed": 565,
            "failed": 5,
            "queued": 10,
            "success_rate": 0.974,
            "avg_processing_time_sec": 42.5,
            "p95_processing_time_sec": 85,
            "total_output_bytes": 52428800000
        }
    """
    period = request.args.get('period', '24h')

    # Parse period to hours
    period_map = {
        '24h': 24,
        '7d': 24 * 7,
        '30d': 24 * 30
    }

    if period not in period_map:
        return jsonify({
            'error': {
                'code': 'INVALID_PERIOD',
                'message': 'period must be one of: 24h, 7d, 30d'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 400

    hours = period_map[period]
    stats = tracker.get_stats(period_hours=hours)

    return jsonify(stats), 200


if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=8005,
        debug=config.DEBUG
    )
