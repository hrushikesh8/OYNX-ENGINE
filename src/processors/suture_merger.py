import cv2
import numpy as np
import subprocess
import os

def get_frame_fingerprint(frame):
    """Converts a frame to a small grayscale matrix for fast comparison."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.resize(gray, (64, 64))

def find_overlap_match(part1, part2, scan_duration=60):
    """Uses CV to find the exact frame where Part 2 begins inside Part 1."""
    cap1 = cv2.VideoCapture(part1)
    cap2 = cv2.VideoCapture(part2)
    
    fps = cap1.get(cv2.CAP_PROP_FPS)
    total_f1 = int(cap1.get(cv2.CAP_PROP_FRAME_COUNT))
    search_frames = int(scan_duration * fps)
    
    # Grab the very first frame of Part 2 to use as our 'Target'
    ret2, frame2_start = cap2.read()
    if not ret2: return None
    target_fp = get_frame_fingerprint(frame2_start)
    
    # Start scanning Part 1 from the end back (e.g., last 60 seconds)
    start_scan = max(0, total_f1 - search_frames)
    cap1.set(cv2.CAP_PROP_POS_FRAMES, start_scan)
    
    best_match_idx = -1
    min_diff = float('inf')

    print(f"[CV] Scanning overlap in Part 1 ({scan_duration}s window)...")
    for i in range(start_scan, total_f1):
        ret1, frame1 = cap1.read()
        if not ret1: break
        
        current_fp = get_frame_fingerprint(frame1)
        # Mean Squared Error comparison
        diff = np.mean((current_fp.astype("float") - target_fp.astype("float")) ** 2)
        
        if diff < min_diff:
            min_diff = diff
            best_match_idx = i
        
        if diff < 0.3: # Threshold for a 'perfect' match
            best_match_idx = i
            break

    cap1.release()
    cap2.release()
    return best_match_idx, fps

def run_suture_workflow(file_list, output_path, use_cv=True):
    """
    Main entry point for stitching. 
    If use_cv is True, it will try to find overlaps automatically.
    """
    print("\n--- Onyx Engine: Seamless Suture Activated ---")
    
    list_file = "concat_list.txt"
    
    try:
        with open(list_file, "w", encoding="utf-8") as f:
            for i in range(len(file_list)):
                current_file = file_list[i].replace("\\", "/")
                f.write(f"file '{current_file}'\n")
                
                # If there's a next file, check for overlap to set an 'outpoint'
                if use_cv and i < len(file_list) - 1:
                    match_idx, fps = find_overlap_match(file_list[i], file_list[i+1])
                    if match_idx != -1:
                        outpoint = match_idx / fps
                        f.write(f"outpoint {outpoint}\n")
                        print(f" -> Found seamless match at {outpoint:.2f}s")

        # FFmpeg Suture
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', 
            '-i', list_file, '-c', 'copy', output_path
        ]
        
        subprocess.run(cmd, check=True)
        print(f"\n[SUCCESS] Seamless Movie created: {output_path}")

    finally:
        if os.path.exists(list_file): os.remove(list_file)