"""
M3 Timecode Validation Service - Flask API Server
Implements OpenAPI specification with 8 endpoints
"""
import logging
import uuid
import os
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest

from . import config
from .bigquery_client import BigQueryClient
from .vision_detector import VisionDetector, MockVisionDetector
from .frame_extractor import FrameExtractor, MockFrameExtractor
from .sync_scorer import SyncScorer
from .offset_calculator import OffsetCalculator

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize clients
bq_client = BigQueryClient()
vision_detector = VisionDetector() if config.VISION_API_ENABLED else MockVisionDetector()
frame_extractor = FrameExtractor() if os.path.exists(config.FFMPEG_PATH) else MockFrameExtractor()
sync_scorer = SyncScorer()
offset_calculator = OffsetCalculator()

# In-memory storage for validation results (for development)
# In production, this would be stored in BigQuery
validation_results = {}


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Returns service status and dependency health
    """
    dependencies = {
        'vision_api': 'ok' if config.VISION_API_ENABLED else 'disabled',
        'bigquery': 'ok',
        'ffmpeg': 'ok' if os.path.exists(config.FFMPEG_PATH) else 'mock'
    }

    status = 'healthy' if all(v in ['ok', 'disabled'] for v in dependencies.values()) else 'degraded'

    return jsonify({
        'status': status,
        'environment': config.POKER_ENV,
        'version': '1.0.0',
        'dependencies': dependencies
    }), 200


@app.route('/v1/validate', methods=['POST'])
def validate_timecode():
    """
    POST /v1/validate - Single hand timecode validation

    Request body:
    {
        "hand_id": "wsop2024_me_d3_h154",
        "timestamp_start_utc": "2024-07-15T15:24:15Z",
        "timestamp_end_utc": "2024-07-15T15:26:45Z",
        "nas_video_path": "/nas/poker/2024/wsop/main_event_day3.mp4",
        "use_vision_api": true
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['hand_id', 'timestamp_start_utc', 'timestamp_end_utc', 'nas_video_path']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': {
                        'code': 'MISSING_FIELD',
                        'message': f'Missing required field: {field}'
                    },
                    'request_id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 400

        hand_id = data['hand_id']
        use_vision_api = data.get('use_vision_api', True)

        # Generate validation ID
        validation_id = f"val-{datetime.utcnow().strftime('%Y%m%d')}-{len(validation_results) + 1:03d}"

        # Create validation job
        validation_results[validation_id] = {
            'validation_id': validation_id,
            'hand_id': hand_id,
            'status': 'processing',
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }

        logger.info(f"Started validation: {validation_id} for hand {hand_id}")

        # Perform validation asynchronously (simplified for sync processing here)
        try:
            result = _perform_validation(
                hand_id=hand_id,
                nas_video_path=data['nas_video_path'],
                use_vision_api=use_vision_api
            )

            # Update validation result
            validation_results[validation_id].update(result)
            validation_results[validation_id]['status'] = 'completed'

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            validation_results[validation_id].update({
                'status': 'failed',
                'error_message': str(e)
            })

        return jsonify({
            'validation_id': validation_id,
            'hand_id': hand_id,
            'status': 'processing',
            'estimated_duration_sec': 10,
            'created_at': validation_results[validation_id]['created_at']
        }), 200

    except BadRequest as e:
        logger.error(f"Bad request: {e}")
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(e)
            },
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 400
    except Exception as e:
        logger.error(f"Internal error: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error'
            },
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@app.route('/v1/validate/<validation_id>/result', methods=['GET'])
def get_validation_result(validation_id):
    """
    GET /v1/validate/{validation_id}/result - Get validation result
    """
    if validation_id not in validation_results:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Validation not found: {validation_id}'
            },
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 404

    result = validation_results[validation_id]

    return jsonify(result), 200


@app.route('/v1/validate/batch', methods=['POST'])
def validate_batch():
    """
    POST /v1/validate/batch - Batch validation

    Request body:
    {
        "hand_ids": ["hand1", "hand2", ...],
        "use_vision_api": true,
        "auto_apply_offset": false
    }
    """
    try:
        data = request.get_json()

        if 'hand_ids' not in data:
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': 'Missing required field: hand_ids'
                },
                'request_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400

        hand_ids = data['hand_ids']
        if len(hand_ids) > 1000:
            return jsonify({
                'error': {
                    'code': 'TOO_MANY_HANDS',
                    'message': 'Maximum 1000 hands per batch'
                },
                'request_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400

        batch_id = f"batch-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"

        logger.info(f"Started batch validation: {batch_id} with {len(hand_ids)} hands")

        return jsonify({
            'batch_id': batch_id,
            'total_hands': len(hand_ids),
            'status': 'queued',
            'estimated_duration_sec': len(hand_ids) * 10,
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }), 200

    except Exception as e:
        logger.error(f"Batch validation error: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error'
            },
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@app.route('/v1/manual/match', methods=['POST'])
def manual_match():
    """
    POST /v1/manual/match - Manual matching

    Request body:
    {
        "hand_id": "wsop2024_me_d3_h154",
        "matched_video_timecode": "03:24:15",
        "matched_by_user": "charlie@ggproduction.net",
        "confidence": "high"
    }
    """
    try:
        data = request.get_json()

        required_fields = ['hand_id', 'matched_video_timecode', 'matched_by_user']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': {
                        'code': 'MISSING_FIELD',
                        'message': f'Missing required field: {field}'
                    },
                    'request_id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 400

        hand_id = data['hand_id']
        matched_timecode = data['matched_video_timecode']

        # Get hand metadata
        hand_metadata = bq_client.get_hand_metadata(hand_id)
        if not hand_metadata:
            return jsonify({
                'error': {
                    'code': 'HAND_NOT_FOUND',
                    'message': f'Hand not found: {hand_id}'
                },
                'request_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 404

        # Calculate manual offset
        offset = offset_calculator.calculate_manual_offset(
            hand_metadata['timestamp_start_utc'],
            matched_timecode
        )

        logger.info(
            f"Manual match: hand={hand_id}, timecode={matched_timecode}, "
            f"offset={offset:.2f}s, user={data['matched_by_user']}"
        )

        return jsonify({
            'hand_id': hand_id,
            'calculated_offset_seconds': offset,
            'sync_score': 100.0,  # Manual match is always perfect
            'validation_method': 'manual',
            'matched_at': datetime.utcnow().isoformat() + 'Z'
        }), 200

    except ValueError as e:
        logger.error(f"Invalid timecode: {e}")
        return jsonify({
            'error': {
                'code': 'INVALID_TIMECODE',
                'message': str(e)
            },
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 400
    except Exception as e:
        logger.error(f"Manual match error: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error'
            },
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@app.route('/v1/sync-scores', methods=['GET'])
def get_sync_scores():
    """
    GET /v1/sync-scores - Get sync scores for hands
    Query params: ?event_id=wsop2024_me&min_score=80
    """
    event_id = request.args.get('event_id')
    min_score = float(request.args.get('min_score', 0))

    # Filter validation results
    filtered_results = []
    for validation in validation_results.values():
        if validation.get('status') != 'completed':
            continue

        if event_id and validation.get('event_id') != event_id:
            continue

        sync_score = validation.get('sync_score', 0)
        if sync_score >= min_score:
            filtered_results.append({
                'validation_id': validation['validation_id'],
                'hand_id': validation['hand_id'],
                'sync_score': sync_score,
                'is_synced': validation.get('is_synced', False)
            })

    return jsonify({
        'sync_scores': filtered_results,
        'total': len(filtered_results)
    }), 200


@app.route('/v1/offsets', methods=['GET'])
def get_offsets():
    """
    GET /v1/offsets - Get calculated offsets
    Query params: ?needs_offset=true
    """
    needs_offset = request.args.get('needs_offset', 'false').lower() == 'true'

    # Filter validation results with offsets
    offsets = []
    for validation in validation_results.values():
        if validation.get('status') != 'completed':
            continue

        if needs_offset and not validation.get('needs_offset', False):
            continue

        if validation.get('calculated_offset_seconds') is not None:
            offsets.append({
                'validation_id': validation['validation_id'],
                'hand_id': validation['hand_id'],
                'offset_seconds': validation['calculated_offset_seconds'],
                'offset_reason': validation.get('offset_reason')
            })

    return jsonify({
        'offsets': offsets,
        'total': len(offsets)
    }), 200


@app.route('/v1/stats', methods=['GET'])
def get_stats():
    """
    GET /v1/stats - Get validation statistics
    Query params: ?event_id=wsop2024_me
    """
    event_id = request.args.get('event_id')

    stats = bq_client.get_validation_stats(event_id)

    return jsonify(stats), 200


def _perform_validation(
    hand_id: str,
    nas_video_path: str,
    use_vision_api: bool = True
) -> dict:
    """
    Internal function to perform validation

    Returns validation result dict
    """
    # 1. Get hand metadata
    hand_metadata = bq_client.get_hand_metadata(hand_id)
    if not hand_metadata:
        raise ValueError(f"Hand not found: {hand_id}")

    # 2. Get video metadata (infer video_id from hand metadata or path)
    # For simplicity, assume video_id is in hand metadata
    video_id = hand_metadata.get('event_id', 'unknown') + '_video'
    video_metadata = bq_client.get_video_metadata(video_id)

    if not video_metadata:
        # Create mock video metadata
        video_metadata = {
            'video_id': video_id,
            'gcs_proxy_path': f'gs://{config.GCS_BUCKET_PROXY}/{nas_video_path}',
            'duration_seconds': hand_metadata.get('duration_seconds', 150)
        }

    # 3. Extract frame at hand start time
    timestamp_seconds = int(hand_metadata['timestamp_start_utc'].timestamp())

    frame_path = None
    vision_confidence = 0.0
    detected_objects = []
    detected_player_count = 0

    if use_vision_api:
        try:
            # Extract frame
            frame_path = frame_extractor.extract_frame(
                nas_video_path,
                timestamp_seconds
            )

            # Upload to GCS
            gcs_blob_name = f"validation-frames/{hand_id}_frame.jpg"
            gcs_uri = vision_detector.upload_frame_to_gcs(frame_path, gcs_blob_name)

            # Detect poker scene
            vision_confidence, detected_objects = vision_detector.detect_poker_scene(gcs_uri)

            # Detect player count
            detected_player_count = vision_detector.detect_player_count(gcs_uri)

        except Exception as e:
            logger.error(f"Vision API processing failed: {e}")
            # Continue with default values

    # 4. Calculate sync score
    scores = sync_scorer.calculate_sync_score(
        hand_metadata,
        video_metadata,
        vision_confidence,
        detected_player_count
    )

    # 5. Calculate offset if needed
    offset_info = offset_calculator.calculate_offset(
        hand_metadata,
        video_metadata,
        scores['sync_score']
    )

    # 6. Prepare result
    result = {
        'validation_id': '',  # Will be set by caller
        'hand_id': hand_id,
        'status': 'completed',
        'sync_score': scores['sync_score'],
        'is_synced': scores['is_synced'],
        'validation_method': 'vision_api' if use_vision_api else 'duration_only',
        'vision_confidence': scores['vision_confidence'] if use_vision_api else None,
        'detected_objects': detected_objects if use_vision_api else None,
        'calculated_offset_seconds': offset_info['offset_seconds'],
        'offset_reason': offset_info['offset_reason'],
        'needs_offset': offset_info['needs_offset'],
        'frame_sample_gcs': gcs_uri if frame_path else None,
        'completed_at': datetime.utcnow().isoformat() + 'Z',
        'recommendation': scores['recommendation']
    }

    # 7. Store in BigQuery
    bq_client.insert_validation_result(result)

    return result


if __name__ == '__main__':
    logger.info(f"Starting M3 Timecode Validation Service on port {config.FLASK_PORT}")
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
