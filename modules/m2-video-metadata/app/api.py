"""
M2 Video Metadata Service - Flask API Server
"""
import os
import uuid
import logging
import threading
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException

from .config import config
from .scanner import NASScanner
from .ffmpeg_utils import FFmpegMetadataExtractor
from .proxy_generator import ProxyGenerator
from .gcs_uploader import GCSUploader
from .bigquery_client import BigQueryClient

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize services
scanner = NASScanner()
ffmpeg_extractor = FFmpegMetadataExtractor()
proxy_gen = ProxyGenerator()
gcs_uploader = GCSUploader()
bq_client = BigQueryClient()

# In-memory job tracking
scan_jobs = {}
proxy_jobs = {}
jobs_lock = threading.Lock()


def generate_scan_id() -> str:
    """Generate scan job ID: scan-YYYYMMDD-NNN"""
    date_str = datetime.now().strftime("%Y%m%d")
    counter = len([k for k in scan_jobs.keys() if date_str in k]) + 1
    return f"scan-{date_str}-{counter:03d}"


def generate_proxy_job_id() -> str:
    """Generate proxy job ID: proxy-YYYYMMDD-NNN"""
    date_str = datetime.now().strftime("%Y%m%d")
    counter = len([k for k in proxy_jobs.keys() if date_str in k]) + 1
    return f"proxy-{date_str}-{counter:03d}"


def process_scan_job(scan_id: str, nas_path: str, recursive: bool, generate_proxy: bool):
    """
    Background task to process scan job

    Args:
        scan_id: Scan job ID
        nas_path: NAS directory path
        recursive: Whether to scan recursively
        generate_proxy: Whether to generate proxies
    """
    try:
        with jobs_lock:
            scan_jobs[scan_id]['status'] = 'running'

        logger.info(f"[{scan_id}] Starting scan of {nas_path}")

        # Step 1: Scan NAS directory
        videos = scanner.scan_directory(nas_path, recursive=recursive)

        with jobs_lock:
            scan_jobs[scan_id]['total_files'] = len(videos)

        logger.info(f"[{scan_id}] Found {len(videos)} videos")

        # Step 2: Process each video
        processed_count = 0
        failed_count = 0
        proxy_count = 0
        failed_files = []

        for video in videos:
            try:
                # Extract metadata using FFmpeg
                metadata = ffmpeg_extractor.extract_metadata(video['nas_file_path'])
                video.update(metadata)

                # Generate proxy if requested
                if generate_proxy:
                    try:
                        # Create temp output path
                        temp_dir = tempfile.gettempdir()
                        proxy_filename = proxy_gen.generate_proxy_filename(video['video_id'])
                        temp_proxy_path = os.path.join(temp_dir, proxy_filename)

                        # Generate proxy
                        proxy_result = proxy_gen.generate_720p_proxy(
                            video['nas_file_path'],
                            temp_proxy_path,
                            quality='medium'
                        )

                        # Upload to GCS
                        blob_name = proxy_gen.generate_gcs_blob_name(
                            video['video_id'],
                            video['event_id']
                        )
                        gcs_path = gcs_uploader.upload_file(temp_proxy_path, blob_name)

                        # Update video metadata
                        video['gcs_proxy_path'] = gcs_path
                        video['proxy_size_bytes'] = proxy_result['output_size_bytes']

                        # Clean up temp file
                        if os.path.exists(temp_proxy_path):
                            os.remove(temp_proxy_path)

                        proxy_count += 1

                    except Exception as proxy_error:
                        logger.error(f"[{scan_id}] Proxy generation failed for {video['video_id']}: {proxy_error}")
                        # Continue without proxy

                # Insert/update in BigQuery
                bq_client.upsert_video_metadata(video)

                processed_count += 1

                with jobs_lock:
                    scan_jobs[scan_id]['processed_files'] = processed_count
                    scan_jobs[scan_id]['proxy_generated'] = proxy_count

            except Exception as e:
                logger.error(f"[{scan_id}] Failed to process {video.get('nas_file_path')}: {e}")
                failed_count += 1
                failed_files.append({
                    'file_path': video.get('nas_file_path'),
                    'error': str(e)
                })

                with jobs_lock:
                    scan_jobs[scan_id]['failed_files'] = failed_count

        # Mark scan as completed
        with jobs_lock:
            scan_jobs[scan_id]['status'] = 'completed'
            scan_jobs[scan_id]['completed_at'] = datetime.utcnow().isoformat()
            scan_jobs[scan_id]['failed_files_list'] = failed_files

        logger.info(f"[{scan_id}] Scan completed. Processed: {processed_count}, Failed: {failed_count}, Proxies: {proxy_count}")

    except Exception as e:
        logger.error(f"[{scan_id}] Scan failed: {e}")
        with jobs_lock:
            scan_jobs[scan_id]['status'] = 'failed'
            scan_jobs[scan_id]['error'] = str(e)


def process_proxy_job(proxy_job_id: str, video: dict, quality: str):
    """
    Background task to generate proxy for a single video

    Args:
        proxy_job_id: Proxy job ID
        video: Video metadata dict
        quality: Quality preset
    """
    try:
        with jobs_lock:
            proxy_jobs[proxy_job_id]['status'] = 'processing'

        video_id = video['video_id']
        nas_path = video['nas_file_path']

        logger.info(f"[{proxy_job_id}] Generating proxy for {video_id}")

        # Create temp output path
        temp_dir = tempfile.gettempdir()
        proxy_filename = proxy_gen.generate_proxy_filename(video_id)
        temp_proxy_path = os.path.join(temp_dir, proxy_filename)

        # Generate proxy
        start_time = datetime.utcnow()
        proxy_result = proxy_gen.generate_720p_proxy(nas_path, temp_proxy_path, quality=quality)
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Upload to GCS
        blob_name = proxy_gen.generate_gcs_blob_name(video_id, video['event_id'])
        gcs_path = gcs_uploader.upload_file(temp_proxy_path, blob_name)
        public_url = gcs_uploader.get_public_url(blob_name)

        # Update BigQuery
        video['gcs_proxy_path'] = gcs_path
        video['proxy_size_bytes'] = proxy_result['output_size_bytes']
        bq_client.upsert_video_metadata(video)

        # Clean up temp file
        if os.path.exists(temp_proxy_path):
            os.remove(temp_proxy_path)

        # Update job status
        with jobs_lock:
            proxy_jobs[proxy_job_id]['status'] = 'completed'
            proxy_jobs[proxy_job_id]['duration_sec'] = int(duration)
            proxy_jobs[proxy_job_id]['output_url'] = public_url
            proxy_jobs[proxy_job_id]['output_size_bytes'] = proxy_result['output_size_bytes']
            proxy_jobs[proxy_job_id]['completed_at'] = datetime.utcnow().isoformat()

        logger.info(f"[{proxy_job_id}] Proxy generation completed in {duration:.1f}s")

    except Exception as e:
        logger.error(f"[{proxy_job_id}] Proxy generation failed: {e}")
        with jobs_lock:
            proxy_jobs[proxy_job_id]['status'] = 'failed'
            proxy_jobs[proxy_job_id]['error_message'] = str(e)


# ==================== API Endpoints ====================

@app.route('/v1/scan', methods=['POST'])
def start_scan():
    """Start NAS directory scan"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request body is required'
                }
            }), 400

        nas_path = data.get('nas_path')
        if not nas_path:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'nas_path is required'
                }
            }), 400

        recursive = data.get('recursive', True)
        generate_proxy = data.get('generate_proxy', True)

        # Generate scan ID
        scan_id = generate_scan_id()

        # Initialize scan job
        scan_jobs[scan_id] = {
            'scan_id': scan_id,
            'status': 'queued',
            'nas_path': nas_path,
            'recursive': recursive,
            'generate_proxy': generate_proxy,
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'proxy_generated': 0,
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': None,
            'failed_files_list': []
        }

        # Start background thread
        thread = threading.Thread(
            target=process_scan_job,
            args=(scan_id, nas_path, recursive, generate_proxy)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'scan_id': scan_id,
            'status': 'queued',
            'nas_path': nas_path,
            'started_at': scan_jobs[scan_id]['started_at']
        }), 202

    except Exception as e:
        logger.error(f"Error starting scan: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500


@app.route('/v1/scan/<scan_id>/status', methods=['GET'])
def get_scan_status(scan_id: str):
    """Get scan job status"""
    if scan_id not in scan_jobs:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Scan {scan_id} not found'
            }
        }), 404

    return jsonify(scan_jobs[scan_id]), 200


@app.route('/v1/files/<file_id>', methods=['GET'])
def get_file_metadata(file_id: str):
    """Get video file metadata by ID"""
    try:
        video = bq_client.get_video_by_id(file_id)

        if not video:
            return jsonify({
                'error': {
                    'code': 'NOT_FOUND',
                    'message': f'File {file_id} not found'
                }
            }), 404

        # Add proxy URL if available
        if video.get('gcs_proxy_path'):
            blob_name = video['gcs_proxy_path'].replace(f"gs://{config.GCS_BUCKET}/", "")
            video['proxy_url'] = gcs_uploader.get_public_url(blob_name)

        return jsonify(video), 200

    except Exception as e:
        logger.error(f"Error getting file metadata: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500


@app.route('/v1/files', methods=['GET'])
def list_files():
    """List video files with optional filtering"""
    try:
        event_id = request.args.get('event_id')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        # Validate limits
        limit = min(max(1, limit), 1000)
        offset = max(0, offset)

        videos = bq_client.list_videos(event_id=event_id, limit=limit, offset=offset)

        # Add proxy URLs
        for video in videos:
            if video.get('gcs_proxy_path'):
                blob_name = video['gcs_proxy_path'].replace(f"gs://{config.GCS_BUCKET}/", "")
                video['proxy_url'] = gcs_uploader.get_public_url(blob_name)

        return jsonify({
            'total': len(videos),
            'limit': limit,
            'offset': offset,
            'files': videos
        }), 200

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500


@app.route('/v1/proxy/generate', methods=['POST'])
def generate_proxy():
    """Generate proxy for a single file"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request body is required'
                }
            }), 400

        file_id = data.get('file_id')
        if not file_id:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'file_id is required'
                }
            }), 400

        quality = data.get('quality', 'medium')
        resolution = data.get('resolution', '720p')

        # Get video metadata
        video = bq_client.get_video_by_id(file_id)
        if not video:
            return jsonify({
                'error': {
                    'code': 'NOT_FOUND',
                    'message': f'File {file_id} not found'
                }
            }), 404

        # Generate proxy job ID
        proxy_job_id = generate_proxy_job_id()

        # Estimate duration (rough: 1 hour video = 2 minutes processing)
        estimated_duration = video.get('duration_seconds', 0) * 2

        # Initialize proxy job
        blob_name = proxy_gen.generate_gcs_blob_name(file_id, video['event_id'], resolution)
        output_gcs_path = f"gs://{config.GCS_BUCKET}/{blob_name}"

        proxy_jobs[proxy_job_id] = {
            'proxy_job_id': proxy_job_id,
            'file_id': file_id,
            'status': 'queued',
            'estimated_duration_sec': estimated_duration,
            'output_gcs_path': output_gcs_path,
            'output_url': None,
            'output_size_bytes': None,
            'duration_sec': None,
            'error_message': None,
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': None
        }

        # Start background thread
        thread = threading.Thread(
            target=process_proxy_job,
            args=(proxy_job_id, video, quality)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'proxy_job_id': proxy_job_id,
            'file_id': file_id,
            'status': 'queued',
            'estimated_duration_sec': estimated_duration,
            'output_gcs_path': output_gcs_path,
            'started_at': proxy_jobs[proxy_job_id]['started_at']
        }), 202

    except Exception as e:
        logger.error(f"Error generating proxy: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500


@app.route('/v1/proxy/<proxy_job_id>/status', methods=['GET'])
def get_proxy_status(proxy_job_id: str):
    """Get proxy generation job status"""
    if proxy_job_id not in proxy_jobs:
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Proxy job {proxy_job_id} not found'
            }
        }), 404

    return jsonify(proxy_jobs[proxy_job_id]), 200


@app.route('/v1/stats', methods=['GET'])
def get_stats():
    """Get scanning statistics"""
    try:
        period = request.args.get('period', '24h')

        if period not in ['24h', '7d', '30d', 'all']:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'period must be one of: 24h, 7d, 30d, all'
                }
            }), 400

        stats = bq_client.get_stats(period=period)

        # Add total files in DB count
        query = f"SELECT COUNT(*) as total FROM `{config.bigquery_table_id}`"
        results = list(bq_client.client.query(query))
        if results:
            stats['total_files_in_db'] = dict(results[0])['total']

        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Service health check"""
    from . import __version__
    import time

    start_time = getattr(app, 'start_time', time.time())
    uptime = int(time.time() - start_time)

    # Check dependencies
    dependencies = {
        'nas': 'ok',
        'bigquery': 'ok',
        'gcs': 'ok'
    }

    # Check NAS mount
    if not os.path.exists(config.NAS_BASE_PATH):
        dependencies['nas'] = 'error'

    # Check BigQuery
    try:
        bq_client.client.query("SELECT 1").result()
    except Exception:
        dependencies['bigquery'] = 'error'

    # Check GCS
    try:
        gcs_uploader.bucket.exists()
    except Exception:
        dependencies['gcs'] = 'error'

    status = 'healthy' if all(v == 'ok' for v in dependencies.values()) else 'degraded'

    return jsonify({
        'status': status,
        'version': __version__,
        'uptime_seconds': uptime,
        'dependencies': dependencies
    }), 200


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Resource not found'
        }
    }), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }
    }), 500


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    return jsonify({
        'error': {
            'code': 'HTTP_ERROR',
            'message': e.description
        }
    }), e.code


# Initialize on startup
@app.before_first_request
def initialize():
    """Initialize service on first request"""
    import time
    app.start_time = time.time()

    logger.info("Initializing M2 Video Metadata Service")

    # Ensure BigQuery table exists
    try:
        bq_client.ensure_table_exists()
        logger.info("BigQuery table initialized")
    except Exception as e:
        logger.error(f"Failed to initialize BigQuery table: {e}")


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=config.PORT,
        debug=False
    )
