import cv2
import pytesseract
import os
import re

# IMPORTANT: You need to tell pytesseract where the Tesseract-OCR executable is.
# If you added Tesseract to your system PATH, you might not need this line.
# If not, uncomment and set the path to your Tesseract installation.
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def analyze_pot_size(video_path):
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Analyzing pot size for video: {os.path.basename(video_path)}")

    # ROI for the pot size, based on generate_sample_video.py
    # x_start, y_start, x_end, y_end
    roi = (490, 720 - 120, 790, 720 - 50)

    last_pot_size = 0

    for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break

        # Process every 15th frame to save time
        if i % 15 == 0:
            # Extract the region of interest
            pot_roi = frame[roi[1]:roi[3], roi[0]:roi[2]]

            # Convert to grayscale for better OCR results
            gray_roi = cv2.cvtColor(pot_roi, cv2.COLOR_BGR2GRAY)

            # Use Tesseract to do OCR on the ROI
            text = pytesseract.image_to_string(gray_roi, config='--psm 6 -c tessedit_char_whitelist=0123456789Pot:')
            
            # Clean up the extracted text
            # Find all digits in the string
            numbers = re.findall(r'\d+', text)
            if numbers:
                current_pot_size = int("".join(numbers))
                if current_pot_size != last_pot_size:
                    timestamp = i / fps
                    print(f"Time: {timestamp:.2f}s - Detected Pot Size: {current_pot_size}")
                    last_pot_size = current_pot_size

    cap.release()
    print("\n--- Pot Size Analysis Complete ---")

if __name__ == "__main__":
    video_to_analyze = os.path.join("videos", "sample_poker_video.mp4")
    analyze_pot_size(video_to_analyze)
