"""
Flask API Server for M1 Data Ingestion Service

Endpoints:
- POST /v1/ingest: Start ingestion job
- GET /v1/ingest/{job_id}/status: Get job status
- GET /v1/stats: Get ingestion statistics
- GET /health: Health check
"""
import logging
import uuid
import threading
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify, Response
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

from .config import Config, get_config
from .dataflow_pipeline import run_pipeline
from .bigquery_client import get_bigquery_client


# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(get_config())

# In-memory job storage (for Week 3 - will use Firestore/Redis in Week 4)
job_status_store: Dict[str, Dict[str, Any]] = {}


def generate_job_id() -> str:
    """Generate unique job ID in format: ingest-YYYYMMDD-NNN"""
    timestamp = datetime.utcnow().strftime('%Y%m%d')

    # Count jobs from today
    today_jobs = [
        job_id for job_id in job_status_store.keys()
        if job_id.startswith(f'ingest-{timestamp}')
    ]

    sequence = len(today_jobs) + 1
    return f"ingest-{timestamp}-{sequence:03d}"


def run_pipeline_async(job_id: str, gcs_path: str, event_id: str, tournament_day: int = None):
    """
    Run pipeline in background thread

    Args:
        job_id: Job ID
        gcs_path: GCS file path
        event_id: Event ID
        tournament_day: Tournament day (optional)
    """
    try:
        logger.info(f"Starting pipeline for job {job_id}")

        # Update status to running
        job_status_store[job_id]['status'] = 'processing'
        job_status_store[job_id]['started_at'] = datetime.utcnow().isoformat()

        # Run pipeline
        dataflow_job_id = run_pipeline(
            gcs_path=gcs_path,
            job_name=job_id.replace('ingest-', 'ati-ingestion-')
        )

        # Update status to completed
        job_status_store[job_id]['status'] = 'completed'
        job_status_store[job_id]['dataflow_job_id'] = dataflow_job_id
        job_status_store[job_id]['completed_at'] = datetime.utcnow().isoformat()

        logger.info(f"Pipeline completed for job {job_id}")

    except Exception as e:
        logger.error(f"Pipeline failed for job {job_id}: {e}", exc_info=True)

        # Update status to failed
        job_status_store[job_id]['status'] = 'failed'
        job_status_store[job_id]['error'] = str(e)
        job_status_store[job_id]['completed_at'] = datetime.utcnow().isoformat()


@app.route('/v1/ingest', methods=['POST'])
def ingest():
    """
    POST /v1/ingest
    Start ATI data ingestion job

    Request body:
        {
            "gcs_path": "gs://bucket/path/file.jsonl",
            "event_id": "wsop2024_me",
            "tournament_day": 3
        }

    Returns:
        202 Accepted: Job queued
        400 Bad Request: Invalid input
    """
    try:
        # Parse request
        data = request.get_json()

        if not data:
            raise BadRequest("Request body is required")

        gcs_path = data.get('gcs_path')
        event_id = data.get('event_id')
        tournament_day = data.get('tournament_day')

        # Validate required fields
        if not gcs_path:
            raise BadRequest("gcs_path is required")

        if not event_id:
            raise BadRequest("event_id is required")

        # Validate GCS path format
        if not gcs_path.startswith('gs://'):
            raise BadRequest("gcs_path must start with 'gs://'")

        if not gcs_path.endswith('.jsonl'):
            raise BadRequest("gcs_path must end with '.jsonl'")

        # Generate job ID
        job_id = generate_job_id()

        # Create job record
        job_record = {
            'job_id': job_id,
            'status': 'queued',
            'gcs_path': gcs_path,
            'event_id': event_id,
            'tournament_day': tournament_day,
            'created_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'completed_at': None,
            'dataflow_job_id': None,
            'rows_processed': 0,
            'rows_failed': 0,
            'errors': []
        }

        job_status_store[job_id] = job_record

        # Start pipeline in background thread
        thread = threading.Thread(
            target=run_pipeline_async,
            args=(job_id, gcs_path, event_id, tournament_day),
            daemon=True
        )
        thread.start()

        logger.info(f"Ingestion job created: {job_id}", extra={'event_id': event_id})

        # Return response
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'gcs_path': gcs_path,
            'event_id': event_id,
            'created_at': job_record['created_at']
        }), 202

    except BadRequest as e:
        logger.warning(f"Bad request: {e.description}")
        return jsonify({
            'error': {
                'code': 'INVALID_REQUEST',
                'message': e.description
            },
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat()
        }), 400

    except Exception as e:
        logger.error(f"Internal error in /v1/ingest: {e}", exc_info=True)
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to start ingestion job'
            },
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/v1/ingest/<job_id>/status', methods=['GET'])
def get_job_status(job_id: str):
    """
    GET /v1/ingest/{job_id}/status
    Get ingestion job status

    Returns:
        200 OK: Job status
        404 Not Found: Job not found
    """
    try:
        # Check if job exists
        if job_id not in job_status_store:
            raise NotFound(f"Job not found: {job_id}")

        job = job_status_store[job_id]

        # Return job status
        return jsonify(job), 200

    except NotFound as e:
        logger.warning(f"Job not found: {job_id}")
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e.description)
            },
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat()
        }), 404

    except Exception as e:
        logger.error(f"Internal error in /v1/ingest/{job_id}/status: {e}", exc_info=True)
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get job status'
            },
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/v1/stats', methods=['GET'])
def get_stats():
    """
    GET /v1/stats
    Get ingestion statistics from BigQuery

    Query params:
        period: 24h, 7d, 30d, all (default: 24h)
        event_id: Filter by event_id (optional)

    Returns:
        200 OK: Statistics
    """
    try:
        # Get query parameters
        period = request.args.get('period', '24h')
        event_id = request.args.get('event_id')

        # Validate period
        if period not in ['24h', '7d', '30d', 'all']:
            raise BadRequest(f"Invalid period: {period}. Must be one of: 24h, 7d, 30d, all")

        # Get stats from BigQuery
        bq_client = get_bigquery_client()
        stats = bq_client.get_stats(period=period, event_id=event_id)

        logger.info(f"Stats retrieved: period={period}, event_id={event_id}")

        return jsonify(stats), 200

    except BadRequest as e:
        logger.warning(f"Bad request: {e.description}")
        return jsonify({
            'error': {
                'code': 'INVALID_REQUEST',
                'message': e.description
            },
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat()
        }), 400

    except Exception as e:
        logger.error(f"Internal error in /v1/stats: {e}", exc_info=True)
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get statistics'
            },
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    GET /health
    Health check endpoint for load balancer

    Returns:
        200 OK: Service is healthy
    """
    try:
        # Check BigQuery connection
        bq_client = get_bigquery_client()
        bq_status = "ok" if bq_client.validate_connection() else "error"

        # Calculate uptime (simplified for Week 3)
        uptime_seconds = 0  # Will implement in Week 4

        health_data = {
            'status': 'healthy' if bq_status == 'ok' else 'degraded',
            'version': '1.0.0',
            'uptime_seconds': uptime_seconds,
            'dependencies': {
                'bigquery': bq_status,
                'gcs': 'ok',  # Assumed OK for Week 3
                'pubsub': 'ok'  # Assumed OK for Week 3
            }
        }

        status_code = 200 if health_data['status'] == 'healthy' else 503

        return jsonify(health_data), status_code

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify({
            'status': 'degraded',
            'error': str(e)
        }), 503


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Endpoint not found'
        },
        'request_id': str(uuid.uuid4()),
        'timestamp': datetime.utcnow().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        },
        'request_id': str(uuid.uuid4()),
        'timestamp': datetime.utcnow().isoformat()
    }), 500


if __name__ == '__main__':
    config = app.config
    app.run(
        host='0.0.0.0',
        port=config.get('PORT', 8001),
        debug=config.get('DEBUG', False)
    )
