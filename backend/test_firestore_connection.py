"""
Test Firestore connection and list hands
"""
import os
from google.cloud import firestore

# Set credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"D:\AI\claude01\archive-mam\backend\config\gcp-service-account.json"

# Initialize Firestore client
project_id = "gg-poker-prod"
db = firestore.Client(project=project_id)

print(f"Connecting to Firestore in project: {project_id}")
print(f"Credentials: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
print()

# List all collections
print("Available collections:")
collections = db.collections()
collection_names = [col.id for col in collections]
print(f"   {collection_names}")
print()

# Query hands collection
print("Querying 'hands' collection...")
try:
    hands_ref = db.collection("hands")
    hands = list(hands_ref.limit(5).stream())

    print(f"SUCCESS: Found {len(hands)} hands (showing first 5):")
    for hand in hands:
        hand_data = hand.to_dict()
        print(f"   - Hand ID: {hand.id}")
        print(f"     video_ref_id: {hand_data.get('video_ref_id', 'N/A')}")
        print(f"     stage: {hand_data.get('game_logic', {}).get('stage', 'N/A')}")
        print(f"     pot: {hand_data.get('game_logic', {}).get('pot_final', 'N/A')}")
        print(f"     embedding exists: {'embedding' in hand_data}")
        print()

except Exception as e:
    print(f"ERROR querying hands: {e}")
    import traceback
    traceback.print_exc()
