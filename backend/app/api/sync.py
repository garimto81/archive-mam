"""
Sync API Endpoints for archive-mam

Synchronize data between Firestore and Vertex AI Vector Search.
"""

import logging
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.firestore import get_firestore_service
from app.services.vertex_search import VertexSearchService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync", tags=["Sync"])


# --- Pydantic Models ---

class SyncRequest(BaseModel):
    """Request model for Firestore -> Vertex AI sync"""
    limit: int = Field(default=100, ge=1, le=1000, description="Number of hands to sync")
    video_ref_id: Optional[str] = Field(default=None, description="Filter by specific video_ref_id")
    force_reindex: bool = Field(default=False, description="Force reindex even if embedding exists")


class SyncResponse(BaseModel):
    """Response model for sync operations"""
    success: bool
    hands_processed: int
    hands_indexed: int
    hands_failed: int
    errors: List[str] = []
    message: str


class SyncStatusResponse(BaseModel):
    """Response model for sync status"""
    total_hands_in_firestore: int
    total_hands_in_vertex: int
    hands_without_embeddings: int
    sync_needed: int


# --- API Endpoints ---

@router.post("/firestore-to-vertex", response_model=SyncResponse)
async def sync_firestore_to_vertex(
    request: SyncRequest,
    background_tasks: BackgroundTasks
):
    """
    Sync hands from Firestore to Vertex AI Vector Search.

    Process:
    1. Fetch hands from Firestore (with/without embeddings)
    2. Generate embeddings if missing (using Vertex AI Embedding API)
    3. Index into Vertex AI Vector Search
    4. Update Firestore with embedding metadata

    Args:
        request: Sync parameters (limit, video_id, force_reindex)
        background_tasks: FastAPI background tasks

    Returns:
        Sync result with counts and any errors
    """
    try:
        firestore_service = get_firestore_service()
        vertex_service = VertexSearchService()

        # Fetch hands from Firestore
        if request.force_reindex or request.video_ref_id:
            # Get all hands (with or without embeddings)
            hands = firestore_service.get_all_hands(
                limit=request.limit,
                video_ref_id=request.video_ref_id
            )
            logger.info(f"Fetched {len(hands)} hands from Firestore (force_reindex={request.force_reindex})")
        else:
            # Get only hands without embeddings
            hands = firestore_service.get_hands_without_embeddings(limit=request.limit)
            logger.info(f"Fetched {len(hands)} hands without embeddings")

        if not hands:
            return SyncResponse(
                success=True,
                hands_processed=0,
                hands_indexed=0,
                hands_failed=0,
                message="No hands to sync"
            )

        # Process hands in the background
        background_tasks.add_task(
            _sync_hands_background,
            hands,
            firestore_service,
            vertex_service
        )

        return SyncResponse(
            success=True,
            hands_processed=len(hands),
            hands_indexed=0,  # Will be updated in background
            hands_failed=0,
            message=f"Sync started for {len(hands)} hands (running in background)"
        )

    except Exception as e:
        logger.error(f"Error syncing Firestore to Vertex AI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status():
    """
    Get sync status between Firestore and Vertex AI.

    Returns:
        - Total hands in Firestore
        - Total hands in Vertex AI
        - Hands without embeddings
        - Hands that need syncing
    """
    print("[DEBUG] get_sync_status() called")
    try:
        print("[DEBUG] Calling get_firestore_service()")
        firestore_service = get_firestore_service()
        print(f"[DEBUG] Firestore service initialized: {firestore_service}")

        # Get all hands from Firestore
        all_hands = firestore_service.get_all_hands(limit=1000)
        total_hands_in_firestore = len(all_hands)

        # Get hands without embeddings
        hands_without_embeddings_list = firestore_service.get_hands_without_embeddings(limit=1000)
        hands_without_embeddings = len(hands_without_embeddings_list)

        # Count hands with embeddings (approximation)
        total_hands_in_vertex = total_hands_in_firestore - hands_without_embeddings

        # Sync needed count
        sync_needed = hands_without_embeddings

        return SyncStatusResponse(
            total_hands_in_firestore=total_hands_in_firestore,
            total_hands_in_vertex=total_hands_in_vertex,
            hands_without_embeddings=hands_without_embeddings,
            sync_needed=sync_needed
        )

    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex-hand/{hand_id}")
async def reindex_single_hand(hand_id: str):
    """
    Reindex a single hand by ID.

    Args:
        hand_id: Hand document ID in Firestore

    Returns:
        Success message
    """
    try:
        firestore_service = get_firestore_service()
        vertex_service = VertexSearchService()

        # Get hand from Firestore
        hand = firestore_service.get_hand_by_id(hand_id)

        if not hand:
            raise HTTPException(status_code=404, detail=f"Hand {hand_id} not found in Firestore")

        # Generate summary and embedding
        summary = _generate_hand_summary(hand)
        embedding = await vertex_service.generate_embedding(summary)

        # Index into Vertex AI
        await vertex_service.index_hand(hand_id, embedding, hand)

        # Update Firestore with embedding
        firestore_service.update_hand_embedding(hand_id, embedding, summary)

        logger.info(f"Successfully reindexed hand {hand_id}")

        return {
            "success": True,
            "hand_id": hand_id,
            "message": f"Hand {hand_id} reindexed successfully"
        }

    except Exception as e:
        logger.error(f"Error reindexing hand {hand_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Background Tasks ---

async def _sync_hands_background(
    hands: List[Dict],
    firestore_service,
    vertex_service: VertexSearchService
):
    """
    Background task to sync hands to Vertex AI.

    Args:
        hands: List of hand dictionaries from Firestore
        firestore_service: Firestore service instance
        vertex_service: Vertex AI service instance
    """
    hands_indexed = 0
    hands_failed = 0

    for hand in hands:
        try:
            hand_id = hand.get("hand_id")

            # Generate summary
            summary = _generate_hand_summary(hand)

            # Generate embedding (if not exists or force reindex)
            if not hand.get("embedding"):
                embedding = await vertex_service.generate_embedding(summary)
            else:
                embedding = hand.get("embedding")

            # Index into Vertex AI
            await vertex_service.index_hand(hand_id, embedding, hand)

            # Update Firestore with embedding (if newly generated)
            if not hand.get("embedding"):
                firestore_service.update_hand_embedding(hand_id, embedding, summary)

            hands_indexed += 1
            logger.info(f"Indexed hand {hand_id} ({hands_indexed}/{len(hands)})")

        except Exception as e:
            hands_failed += 1
            logger.error(f"Failed to index hand {hand.get('hand_id')}: {e}")

    logger.info(f"Background sync complete: {hands_indexed} indexed, {hands_failed} failed")


# --- Helper Functions ---

def _generate_hand_summary(hand: Dict) -> str:
    """
    Generate a text summary for a hand (for embedding generation).

    Args:
        hand: Hand dictionary from Firestore

    Returns:
        Text summary string
    """
    summary_parts = []

    # Basic info
    hand_number = hand.get("hand_number", "Unknown")
    video_id = hand.get("video_id", "Unknown")
    summary_parts.append(f"Hand #{hand_number} from video {video_id}")

    # Pot size
    pot_bb = hand.get("pot_bb")
    if pot_bb:
        summary_parts.append(f"Pot: {pot_bb} BB")

    # Players
    players = hand.get("players", [])
    if players:
        player_names = [p.get("name", "Unknown") for p in players]
        summary_parts.append(f"Players: {', '.join(player_names)}")

    # Winner
    winner = hand.get("winner")
    if winner:
        summary_parts.append(f"Winner: {winner}")

    # Board cards
    board = hand.get("board", {})
    flop = board.get("flop", [])
    turn = board.get("turn")
    river = board.get("river")

    if flop:
        summary_parts.append(f"Flop: {', '.join(flop)}")
    if turn:
        summary_parts.append(f"Turn: {turn}")
    if river:
        summary_parts.append(f"River: {river}")

    # Actions summary
    actions = hand.get("actions", [])
    if actions:
        action_summary = f"{len(actions)} actions recorded"
        summary_parts.append(action_summary)

    # Existing summary (if available)
    if hand.get("summary"):
        summary_parts.append(hand.get("summary"))

    return ". ".join(summary_parts)
