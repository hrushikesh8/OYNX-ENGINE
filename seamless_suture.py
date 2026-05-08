import cv2
import numpy as np
import subprocess
import os

def get_frame_fingerprint(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.resize(gray, (64, 64))

def find_merge_indices(part1_path, part2_path, overlap_duration=60):
    cap1 = cv2.VideoCapture(part1_path)
    cap2 = cv2.VideoCapture(part2_path)
    
    fps = cap1.get(cv2.CAP_PROP_FPS)
    total_f1 = int(cap1.get(cv2.CAP_PROP_FRAME_COUNT))
    search_frames = int(overlap_duration * fps)
    
    ret2, frame2_start = cap2.read()
    if not ret2: return None
    target_fp = get_frame_fingerprint(frame2_start)
    
    start_scan = max(0, total_f1 - search_frames)
    cap1.set(cv2.CAP_PROP_POS_FRAMES, start_scan)
    
    best_match_idx = -1
    min_diff = float('inf')

    print(f"Scanning the last {overlap_duration}s for a precise frame match...")
    for i in range(start_scan, total_f1):
        ret1, frame1 = cap1.read()
        if not ret1: break
        
        current_fp = get_frame_fingerprint(frame1)
        diff = np.mean((current_fp.astype("float") - target_fp.astype("float")) ** 2)
        
        if diff < min_diff:
            min_diff = diff
            best_match_idx = i
        
        if diff < 0.3: # Perfect match threshold
            best_match_idx = i
            break

    cap1.release()
    cap2.release()
    return best_match_idx

def execute_final_merge(part1, part2, match_frame, target_folder):
    cap = cv2.VideoCapture(part1)
    fps = cap.get(cv2.CAP_PROP_FPS)
    timestamp = match_frame / fps
    cap.release()

    # Automatically detect if it is an MP4 or MKV
    ext = os.path.splitext(part1)[1].lower()
    base_name = os.path.basename(part1).replace("_First_Half", "").replace(ext, "")
    final_output = os.path.join(target_folder, f"{base_name}_Full_Seamless{ext}")
    list_file = os.path.join(target_folder, "concat_list.txt")

    print(f"---> Match detected at {timestamp:.2f}s.")
    print(f"---> Executing Native Concat Suture for {ext.upper()}...")

    with open(list_file, "w", encoding="utf-8") as f:
        f.write(f"file '{part1.replace(os.sep, '/')}'\n")
        f.write(f"outpoint {timestamp}\n") 
        f.write(f"file '{part2.replace(os.sep, '/')}'\n")

    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', 
        '-i', list_file, '-c', 'copy', final_output
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f"\nSUCCESS: Full Seamless Movie created at:\n{final_output}")
        if os.path.exists(list_file): os.remove(list_file)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] FFmpeg failed during processing: {e}")

def run_suture_workflow(folder_path):
    """The entry point for VidFlow main application."""
    if not os.path.isdir(folder_path):
        print("Invalid directory.")
        return

    # Grabs both MKV and MP4 files, ignores random files like .srt or .txt
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
             if f.lower().endswith(('.mkv', '.mp4'))]
    files.sort()

    if len(files) < 2:
        print("Need at least two video files (.mkv or .mp4) in the folder to merge.")
        return

    p1, p2 = files[0], files[1]
    
    # Quick safety check to prevent MKV + MP4 crashes
    if os.path.splitext(p1)[1].lower() != os.path.splitext(p2)[1].lower():
        print("[ERROR] File extensions do not match. Both parts must be MKV or both must be MP4.")
        return

    match_idx = find_merge_indices(p1, p2, overlap_duration=60)

    if match_idx != -1:
        execute_final_merge(p1, p2, match_idx, folder_path)
    else:
        print("[ERROR] Could not find overlapping frames.")

if __name__ == "__main__":
    # Allows you to still test it independently
    test_folder = input("Enter Folder Path: ").strip().replace('"', '')
    run_suture_workflow(test_folder)