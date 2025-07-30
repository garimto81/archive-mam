
import cv2
import numpy as np
import os

# Video properties
width = 1280
height = 720
fps = 30
duration_seconds = 20
total_frames = fps * duration_seconds

# Output video path
output_dir = "videos"
output_filename = "sample_poker_video.mp4"
output_path = os.path.join(output_dir, output_filename)

os.makedirs(output_dir, exist_ok=True)

# Video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

# Font for text
font = cv2.FONT_HERSHEY_SIMPLEX

def draw_text(frame, text, position, size=2, color=(255, 255, 255)):
    cv2.putText(frame, text, position, font, size, color, 3, cv2.LINE_AA)

def draw_cards(frame, num_cards):
    for i in range(num_cards):
        x = 200 + i * 150
        y = 400
        cv2.rectangle(frame, (x, y), (x + 100, y + 150), (255, 0, 0), -1)

def draw_pot_size(frame, size):
    # Draw a background for the pot size text
    cv2.rectangle(frame, (490, height - 120), (790, height - 50), (0, 0, 0), -1)
    cv2.rectangle(frame, (495, height - 115), (785, height - 55), (50, 50, 50), -1)
    draw_text(frame, f"Pot: {size}", (500, height - 70), 1.5, (0, 255, 255))

# Generate frames
for i in range(total_frames):
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Hand 1
    if 1 * fps <= i < 10 * fps:
        pot = 0
        if 1 * fps <= i < 3 * fps:
            draw_text(frame, "Hand 1 Start", (400, 100))
        elif 3 * fps <= i < 5 * fps:
            draw_text(frame, "Hand 1", (500, 100))
            draw_cards(frame, 2)
            pot = 1500
        elif 5 * fps <= i < 8 * fps:
            draw_text(frame, "Hand 1", (500, 100))
            draw_cards(frame, 2)
            pot = 8750
        elif 8 * fps <= i < 10 * fps:
            draw_text(frame, "Hand 1 End", (450, 100))
        if pot > 0:
            draw_pot_size(frame, pot)

    # Hand 2
    if 11 * fps <= i < 20 * fps:
        pot = 0
        if 11 * fps <= i < 13 * fps:
            draw_text(frame, "Hand 2 Start", (400, 100))
        elif 13 * fps <= i < 16 * fps:
            draw_text(frame, "Hand 2", (500, 100))
            draw_cards(frame, 4)
            pot = 5200
        elif 16 * fps <= i < 18 * fps:
            draw_text(frame, "Hand 2", (500, 100))
            draw_cards(frame, 4)
            pot = 22400
        elif 18 * fps <= i < 20 * fps:
            draw_text(frame, "Hand 2 End", (450, 100))
        if pot > 0:
            draw_pot_size(frame, pot)

    video_writer.write(frame)

video_writer.release()

print(f"Sample video with pot size created at {output_path}")
