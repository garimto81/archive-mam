import cv2
import numpy as np
import os

# --- This is a simplified detector for the sample video. ---
# --- In a real scenario, this would be a more complex CV or OCR model. ---

def detect_text_in_frame(frame, text_to_find):
    # This is a mock function. A real implementation would use OCR.
    # For our sample video, we can cheat by knowing the text and its location.
    # We will check a specific region of the frame for non-black pixels.
    if text_to_find == "Hand Start":
        roi = frame[50:150, 400:880] # Region where "Hand Start" appears
        return np.any(roi)
    elif text_to_find == "Hand End":
        # Corrected ROI for "Hand End", excluding the "Hand Start" region
        roi_end = frame[50:150, 450:830] # Region where "Hand End" appears
        roi_start = frame[50:150, 400:450] # Region specific to "Hand Start"
        return np.any(roi_end) and not np.any(roi_start)
    else:
        return False

def analyze_video(video_path):
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    hand_start_frames = []
    hand_end_frames = []

    print(f"Analyzing video: {os.path.basename(video_path)}")

    for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break

        # We need to check for both start and end text in each frame
        if detect_text_in_frame(frame, "Hand Start"):
            hand_start_frames.append(i)
        
        if detect_text_in_frame(frame, "Hand End"):
            hand_end_frames.append(i)

    cap.release()

    # --- Post-processing to find the first frame of each event ---
    def get_event_start_times(frames, fps):
        if not frames:
            return []
        
        event_starts = [frames[0]]
        for i in range(1, len(frames)):
            # If the current frame is not consecutive to the previous one, it's a new event
            if frames[i] > frames[i-1] + 1:
                event_starts.append(frames[i])
        
        return [f"{s/fps:.2f}s" for s in event_starts]

    start_times = get_event_start_times(hand_start_frames, fps)
    end_times = get_event_start_times(hand_end_frames, fps)

    print("\n--- Analysis Complete ---")
    print(f"Detected Hand Starts at: {start_times}")
    print(f"Detected Hand Ends at:   {end_times}")

if __name__ == "__main__":
    video_to_analyze = os.path.join("videos", "sample_poker_video.mp4")
    analyze_video(video_to_analyze)