"""
Flask API Server for M4 RAG Search Service

Endpoints:
- POST /v1/search: Natural language search
- GET /v1/search/autocomplete: Autocomplete suggestions
- POST /v1/search/feedback: Submit feedback
- GET /v1/favorites: Get user favorites
- GET /v1/similar/{hand_id}: Find similar hands
- POST /v1/admin/reindex: Trigger reindexing
- GET /v1/stats: Search statistics
- GET /health: Health check
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, Response
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized, InternalServerError

from .config import get_config
from .vector_search import get_vector_search
from .autocomplete import get_autocomplete_service
from .bigquery_client import get_bigquery_client
from .embedding_service import get_embedding_service


# Initialize logging
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
vector_search = get_vector_search()
autocomplete_service = get_autocomplete_service()
bq_client = get_bigquery_client()
embedding_service = get_embedding_service()


def generate_query_id() -> str:
    """Generate unique query ID in format: search-YYYYMMDD-NNN"""
    timestamp = datetime.utcnow().strftime('%Y%m%d')
    sequence = str(uuid.uuid4())[:3]  # Use UUID for uniqueness
    return f"search-{timestamp}-{sequence}"


def get_user_id() -> Optional[str]:
    """Extract user ID from JWT token (if auth enabled)"""
    if not config.REQUIRE_AUTH:
        return 'dev-user'

    # In production, extract from JWT token
    # auth_header = request.headers.get('Authorization')
    # if not auth_header or not auth_header.startswith('Bearer '):
    #     raise Unauthorized("Missing or invalid authorization header")
    # token = auth_header.split(' ')[1]
    # user_id = decode_jwt(token)  # Implement JWT decoding
    # return user_id

    return 'dev-user'


@app.route('/v1/search', methods=['POST'])
def search():
    """
    POST /v1/search
    Natural language search for poker hands

    Request body:
        {
            "query": "Tom Dwan bluff",
            "limit": 20,
            "filters": {
                "players": ["Tom Dwan"],
                "event_name_contains": "WSOP",
                "year_range": [2008, 2024],
                "pot_size_min": 100000
            },
            "include_proxy": true
        }

    Returns:
        200 OK: Search results
        400 Bad Request: Invalid input
        500 Internal Server Error
    """
    try:
        # Get user ID (for logging)
        user_id = get_user_id()

        # Parse request
        data = request.get_json()

        if not data:
            raise BadRequest("Request body is required")

        query = data.get('query')
        if not query:
            raise BadRequest("query is required")

        if not isinstance(query, str):
            raise BadRequest("query must be a string")

        query = query.strip()
        if len(query) < config.MIN_QUERY_LENGTH:
            raise BadRequest(
                f"query must be at least {config.MIN_QUERY_LENGTH} characters"
            )

        # Parse parameters
        limit = data.get('limit', config.DEFAULT_TOP_K)
        if not isinstance(limit, int) or limit < 1:
            raise BadRequest("limit must be a positive integer")

        if limit > config.MAX_TOP_K:
            limit = config.MAX_TOP_K

        filters = data.get('filters', {})
        include_proxy = data.get('include_proxy', True)

        # Generate query ID
        query_id = generate_query_id()

        # Execute search
        search_start = datetime.utcnow()
        search_result = vector_search.search(
            query=query,
            top_k=limit,
            filters=filters
        )

        # Format results
        results = []
        for result in search_result['results']:
            formatted_result = {
                'hand_id': result.get('hand_id'),
                'relevance_score': result.get('relevance_score'),
                'summary': result.get('summary_text', ''),
                'tournament_id': result.get('tournament_id'),
                'event_name': result.get('event_name'),
                'timestamp': result.get('timestamp'),
                'players': result.get('players', []),
                'pot_size': result.get('pot_size')
            }

            # Add optional fields
            if 'nas_path' in result:
                formatted_result['nas_path'] = result['nas_path']

            if 'timecode_offset' in result:
                formatted_result['timecode_offset'] = result['timecode_offset']

            if include_proxy and 'proxy_url' in result:
                formatted_result['proxy_url'] = result['proxy_url']

            results.append(formatted_result)

        # Log search
        bq_client.log_search(
            query_id=query_id,
            query_text=query,
            user_id=user_id,
            results_count=len(results),
            processing_time_ms=search_result['processing_time_ms']
        )

        # Return response
        response = {
            'query_id': query_id,
            'total_results': search_result['total_results'],
            'processing_time_ms': search_result['processing_time_ms'],
            'results': results
        }

        # Add debug info if enabled
        if config.DEBUG and search_result.get('debug'):
            response['debug'] = search_result['debug']

        return jsonify(response), 200

    except BadRequest as e:
        logger.warning(f"Bad request: {e}")
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(e)
            }
        }), 400

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@app.route('/v1/search/autocomplete', methods=['GET'])
def autocomplete():
    """
    GET /v1/search/autocomplete?q=Tom%20D&limit=10
    Get autocomplete suggestions

    Query parameters:
        q: Search query (min 2 chars)
        limit: Max suggestions (default 10, max 20)

    Returns:
        200 OK: Suggestions
        400 Bad Request: Invalid input
    """
    try:
        query = request.args.get('q', '').strip()

        if not query:
            raise BadRequest("q parameter is required")

        if len(query) < config.AUTOCOMPLETE_MIN_QUERY_LENGTH:
            raise BadRequest(
                f"q must be at least {config.AUTOCOMPLETE_MIN_QUERY_LENGTH} characters"
            )

        limit = request.args.get('limit', config.AUTOCOMPLETE_LIMIT, type=int)
        if limit < 1 or limit > 20:
            raise BadRequest("limit must be between 1 and 20")

        # Get suggestions
        suggestions = autocomplete_service.get_suggestions(query, limit)

        return jsonify({
            'query': query,
            'suggestions': suggestions
        }), 200

    except BadRequest as e:
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(e)
            }
        }), 400

    except Exception as e:
        logger.error(f"Autocomplete failed: {e}", exc_info=True)
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@app.route('/v1/search/feedback', methods=['POST'])
def submit_feedback():
    """
    POST /v1/search/feedback
    Submit user feedback on search results

    Request body:
        {
            "query_id": "search-20241117-001",
            "hand_id": "HAND_000001",
            "feedback": "relevant"  // or "not_relevant", "favorite"
        }

    Returns:
        200 OK: Feedback saved
        400 Bad Request: Invalid input
    """
    try:
        user_id = get_user_id()

        data = request.get_json()
        if not data:
            raise BadRequest("Request body is required")

        query_id = data.get('query_id')
        hand_id = data.get('hand_id')
        feedback = data.get('feedback')

        if not query_id:
            raise BadRequest("query_id is required")

        if not hand_id:
            raise BadRequest("hand_id is required")

        if feedback not in ['relevant', 'not_relevant', 'favorite']:
            raise BadRequest(
                "feedback must be 'relevant', 'not_relevant', or 'favorite'"
            )

        # Save feedback
        bq_client.save_feedback(
            query_id=query_id,
            hand_id=hand_id,
            user_id=user_id,
            feedback=feedback
        )

        return jsonify({
            'status': 'ok',
            'message': 'Feedback recorded'
        }), 200

    except BadRequest as e:
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(e)
            }
        }), 400

    except Exception as e:
        logger.error(f"Submit feedback failed: {e}", exc_info=True)
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@app.route('/v1/similar/<hand_id>', methods=['GET'])
def find_similar(hand_id: str):
    """
    GET /v1/similar/{hand_id}
    Find similar hands

    Path parameters:
        hand_id: Hand ID

    Query parameters:
        limit: Max results (default 10)

    Returns:
        200 OK: Similar hands
        404 Not Found: Hand not found
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        if limit < 1 or limit > 50:
            raise BadRequest("limit must be between 1 and 50")

        # Find similar hands
        similar_hands = vector_search.find_similar(hand_id, limit)

        return jsonify({
            'hand_id': hand_id,
            'similar_hands': similar_hands
        }), 200

    except BadRequest as e:
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(e)
            }
        }), 400

    except Exception as e:
        logger.error(f"Find similar failed: {e}", exc_info=True)
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@app.route('/v1/admin/reindex', methods=['POST'])
def reindex():
    """
    POST /v1/admin/reindex
    Trigger reindexing of embeddings (admin only)

    Request body:
        {
            "event_id": null,  // optional: reindex specific event
            "force": true
        }

    Returns:
        200 OK: Reindex job started
    """
    try:
        # In development mode, just return mock response
        if config.is_development():
            return jsonify({
                'reindex_job_id': f"reindex-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'status': 'started',
                'estimated_duration_sec': 7200,
                'message': '[MOCK] Reindexing job started'
            }), 200

        # Production implementation would:
        # 1. Validate admin permissions
        # 2. Start Cloud Dataflow job to regenerate embeddings
        # 3. Return job ID for tracking

        return jsonify({
            'error': {
                'code': 'NOT_IMPLEMENTED',
                'message': 'Reindexing not implemented in production yet'
            }
        }), 501

    except Exception as e:
        logger.error(f"Reindex failed: {e}", exc_info=True)
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@app.route('/v1/stats', methods=['GET'])
def get_stats():
    """
    GET /v1/stats?period=24h
    Get search statistics

    Query parameters:
        period: 24h, 7d, 30d (default: 24h)

    Returns:
        200 OK: Search statistics
    """
    try:
        period = request.args.get('period', '24h')

        if period not in ['24h', '7d', '30d']:
            raise BadRequest("period must be '24h', '7d', or '30d'")

        stats = bq_client.get_search_stats(period)

        return jsonify(stats), 200

    except BadRequest as e:
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(e)
            }
        }), 400

    except Exception as e:
        logger.error(f"Get stats failed: {e}", exc_info=True)
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """
    GET /health
    Health check endpoint

    Returns:
        200 OK: Service healthy
        503 Service Unavailable: Service unhealthy
    """
    try:
        # Check dependencies
        dependencies = {
            'bigquery': 'unknown',
            'vertex_ai': 'unknown',
            'mock_data': 'unknown'
        }

        if config.is_development():
            # Check mock data loading
            dependencies['mock_data'] = 'healthy' if bq_client._mock_hands else 'unhealthy'
            dependencies['bigquery'] = 'disabled'
            dependencies['vertex_ai'] = 'disabled'
        else:
            # Check real services
            try:
                # Simple BigQuery connectivity check
                bq_client.client.query("SELECT 1").result()
                dependencies['bigquery'] = 'healthy'
            except Exception:
                dependencies['bigquery'] = 'unhealthy'

            try:
                # Check Vertex AI
                embedding_service.generate_embedding("test")
                dependencies['vertex_ai'] = 'healthy'
            except Exception:
                dependencies['vertex_ai'] = 'unhealthy'

        # Overall status
        status = 'healthy' if all(
            v in ['healthy', 'disabled'] for v in dependencies.values()
        ) else 'unhealthy'

        status_code = 200 if status == 'healthy' else 503

        return jsonify({
            'status': status,
            'environment': config.ENV,
            'dependencies': dependencies
        }), status_code

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Resource not found'
        }
    }), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {e}", exc_info=True)
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred'
        }
    }), 500


if __name__ == '__main__':
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
