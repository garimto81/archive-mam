import cv2
import numpy as np
import os

# Define regions of interest (ROIs) for player seats
# These are based on where cards (blue rectangles) appear in generate_sample_video.py
# Format: (x_start, y_start, x_end, y_end)
PLAYER_SEATS_ROI = {
    "Player 1": (200, 400, 300, 550), # First card in Hand 1
    "Player 2": (350, 400, 450, 550), # Second card in Hand 1
    "Player 3": (500, 400, 600, 550), # Third card in Hand 2
    "Player 4": (650, 400, 750, 550), # Fourth card in Hand 2
}

def detect_player_cards(frame):
    active_players = []
    for player, roi in PLAYER_SEATS_ROI.items():
        x1, y1, x2, y2 = roi
        # Extract the region of interest
        player_roi = frame[y1:y2, x1:x2]
        
        # Check for the presence of blue color (cards are drawn in blue)
        # A simple check: if there are significant blue pixels, assume a card is present
        # This is a simplified check for our sample video.
        # In a real scenario, more robust object detection (e.g., card recognition) would be used.
        blue_channel = player_roi[:, :, 0] # Blue channel
        green_channel = player_roi[:, :, 1] # Green channel
        red_channel = player_roi[:, :, 2] # Red channel

        # Check if blue is significantly higher than red and green
        # And if there are enough non-zero blue pixels
        if np.mean(blue_channel) > np.mean(red_channel) * 1.5 and \
           np.mean(blue_channel) > np.mean(green_channel) * 1.5 and \
           np.count_nonzero(blue_channel > 50) > (player_roi.size / 10): # At least 10% of ROI is blue
            active_players.append(player)
            
    return active_players

def analyze_video_for_players(video_path):
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Analyzing players for video: {os.path.basename(video_path)}")

    last_active_players = []

    for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break

        # Process every 15th frame to save time, or more frequently if needed
        if i % 15 == 0:
            current_active_players = detect_player_cards(frame)
            
            # Only print if there's a change in active players
            if set(current_active_players) != set(last_active_players):
                timestamp = i / fps
                print(f"Time: {timestamp:.2f}s - Active Players: {current_active_players}")
                last_active_players = current_active_players

    cap.release()
    print("\n--- Player Analysis Complete ---")

if __name__ == "__main__":
    video_to_analyze = os.path.join("videos", "sample_poker_video.mp4")
    analyze_video_for_players(video_to_analyze)
