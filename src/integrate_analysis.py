

import cv2
import numpy as np
import os
import pytesseract
import re
import json

# IMPORTANT: Set the path to your Tesseract-OCR executable here.
# If you added Tesseract to your system PATH, you might not need this line,
# but it's good practice to be explicit for robustness.
pytesseract.pytesseract.tesseract_cmd = r'd:\Program Files\Tesseract-OCR\tesseract.exe' # <--- PATH UPDATED

# --- Helper functions (copied/adapted from previous steps) ---

def detect_text_in_frame(frame, text_to_find):
    # Simplified text detection for sample video
    if text_to_find == "Hand Start":
        roi = frame[50:150, 400:880]
        return np.any(roi)
    elif text_to_find == "Hand End":
        roi_end = frame[50:150, 450:830]
        roi_start = frame[50:150, 400:450] # Check if Hand Start is also present
        return np.any(roi_end) and not np.any(roi_start)
    return False

PLAYER_SEATS_ROI = {
    "Player 1": (200, 400, 300, 550),
    "Player 2": (350, 400, 450, 550),
    "Player 3": (500, 400, 600, 550),
    "Player 4": (650, 400, 750, 550),
}

def detect_player_cards(frame):
    active_players = []
    for player, roi in PLAYER_SEATS_ROI.items():
        x1, y1, x2, y2 = roi
        player_roi = frame[y1:y2, x1:x2]
        
        blue_channel = player_roi[:, :, 0]
        green_channel = player_roi[:, :, 1]
        red_channel = player_roi[:, :, 2]

        if np.mean(blue_channel) > np.mean(red_channel) * 1.5 and \
           np.mean(blue_channel) > np.mean(green_channel) * 1.5 and \
           np.count_nonzero(blue_channel > 50) > (player_roi.size / 10):
            active_players.append(player)
            
    return active_players

# ROI for the pot size, based on generate_sample_video.py
POT_SIZE_ROI = (490, 720 - 120, 790, 720 - 50)

def get_pot_size_from_frame(frame):
    x1, y1, x2, y2 = POT_SIZE_ROI
    pot_roi = frame[y1:y2, x1:x2]
    gray_roi = cv2.cvtColor(pot_roi, cv2.COLOR_BGR2GRAY)
    
    # OCR configuration for numbers and 'Pot:' text
    config = '--psm 6 -c tessedit_char_whitelist=0123456789Pot:'
    text = pytesseract.image_to_string(gray_roi, config=config)
    
    numbers = re.findall(r'\d+', text)
    if numbers:
        return int("".join(numbers))
    return None

# --- Main integration logic ---

def analyze_and_structure_video(video_path, output_json_path):
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    all_hands_data = []
    current_hand = None
    hand_id_counter = 0
    last_pot_size = None
    last_active_players = []

    print(f"Integrating analysis for video: {os.path.basename(video_path)}")

    for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = i / fps

        is_hand_start = detect_text_in_frame(frame, "Hand Start")
        is_hand_end = detect_text_in_frame(frame, "Hand End")

        # Hand Start Detection
        if is_hand_start and current_hand is None:
            hand_id_counter += 1
            current_hand = {
                "hand_id": hand_id_counter,
                "start_time_s": round(timestamp, 2),
                "end_time_s": None, # Will be filled when hand ends
                "pot_size_history": [],
                "participating_players": []
            }
            print(f"Detected Hand {hand_id_counter} Start at {timestamp:.2f}s")

        # If a hand is active, collect data
        if current_hand is not None:
            # Pot Size Analysis
            current_pot = get_pot_size_from_frame(frame)
            if current_pot is not None and current_pot != last_pot_size:
                current_hand["pot_size_history"].append({"time_s": round(timestamp, 2), "pot": current_pot})
                last_pot_size = current_pot

            # Player Detection (only at the beginning of the hand or when players change significantly)
            # For simplicity in this sample, we'll just take the players detected at the start of the hand
            # In a real scenario, this would be more dynamic.
            if not current_hand["participating_players"]:
                players = detect_player_cards(frame)
                if players:
                    current_hand["participating_players"] = sorted(list(set(players))) # Ensure unique and sorted

            # Hand End Detection
            if is_hand_end:
                if current_hand["end_time_s"] is None: # Only set once
                    current_hand["end_time_s"] = round(timestamp, 2)
                    all_hands_data.append(current_hand)
                    print(f"Detected Hand {hand_id_counter} End at {timestamp:.2f}s")
                    current_hand = None # Reset for next hand
                    last_pot_size = None # Reset pot size for next hand
                    last_active_players = [] # Reset players for next hand

    cap.release()

    # Save to JSON file
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(all_hands_data, f, ensure_ascii=False, indent=4)

    print(f"\n--- Analysis Complete. Data saved to {output_json_path} ---")

if __name__ == "__main__":
    video_file = os.path.join("videos", "sample_poker_video.mp4")
    output_json = os.path.join("analysis_results", "poker_hands_analysis.json")
    
    # Create analysis_results directory if it doesn't exist
    os.makedirs(os.path.dirname(output_json), exist_ok=True)

    analyze_and_structure_video(video_file, output_json)
