"""
Test to check actual Firestore schema in qwen_hand_analysis
"""
import os
from google.cloud import firestore
from google.oauth2 import service_account
import json

# Set credentials
credentials_path = r"D:\AI\claude01\archive-mam\backend\config\gcp-service-account.json"
project_id = "gg-poker-prod"

# Load credentials with scopes
scopes = [
    'https://www.googleapis.com/auth/datastore',
    'https://www.googleapis.com/auth/cloud-platform'
]
creds = service_account.Credentials.from_service_account_file(
    credentials_path,
    scopes=scopes
)

# Initialize Firestore client
db = firestore.Client(project=project_id, credentials=creds)

print(f"Connecting to Firestore in project: {project_id}")
print()

# Get one hand to inspect schema
print("Fetching one hand to inspect schema...")
try:
    hands_ref = db.collection("hands")
    hands = list(hands_ref.limit(1).stream())

    if hands:
        hand = hands[0]
        hand_data = hand.to_dict()

        print(f"Hand ID: {hand.id}")
        print()
        print("Available fields:")
        for key in sorted(hand_data.keys()):
            value = hand_data[key]
            value_type = type(value).__name__

            # Show first 100 chars of value
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."

            print(f"  {key}: ({value_type}) {value_str}")

        print()
        print("Full data (JSON):")
        print(json.dumps(hand_data, indent=2, default=str))

    else:
        print("No hands found")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
