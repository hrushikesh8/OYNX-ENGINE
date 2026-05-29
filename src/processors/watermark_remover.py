import os
import subprocess
import cv2

def get_watermark_coords(video_path):
    """
    Opens the first frame of the video and allows the user to draw a 
    bounding box over the watermark using their mouse.
    """
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("[ERROR] Could not read video frame.")
        return None

    print("\n[UI] A window will now open.")
    print("1. Drag a box over the watermark.")
    print("2. Press 'SPACE' or 'ENTER' to confirm.")
    print("3. Press 'c' to cancel.")
    
    # Let user select the Region of Interest (ROI)
    roi = cv2.selectROI("Select Watermark (Press ENTER to confirm)", frame, showCrosshair=True, fromCenter=False)
    cv2.destroyAllWindows()

    x, y, w, h = roi
    
    # If the user didn't select anything (w or h is 0)
    if w == 0 or h == 0:
        return None

    # FFmpeg delogo requires even numbers for dimensions
    if w % 2 != 0: w += 1
    if h % 2 != 0: h += 1

    return (int(x), int(y), int(w), int(h))

def run_delogo_workflow(target_path):
    print("\n--- VidFlow: Advanced Delogo Engine ---")
    
    if not os.path.isfile(target_path):
        print("[ERROR] Please provide a valid file path, not a folder.")
        return

    coords = get_watermark_coords(target_path)
    
    if not coords:
        print("[INFO] Selection cancelled or invalid. Aborting.")
        return

    x, y, w, h = coords
    print(f"\n---> Target Locked: X:{x} Y:{y} Width:{w} Height:{h}")
    print("---> Initiating Spatial Interpolation (In-painting)...")

    base_dir = os.path.dirname(target_path)
    ext = os.path.splitext(target_path)[1]
    base_name = os.path.basename(target_path).replace(ext, "")
    output_name = os.path.join(base_dir, f"{base_name}_Cleaned{ext}")

    # -vf delogo applies the spatial interpolation
    # -c:a copy preserves the audio tracks untouched
    cmd = [
        'ffmpeg', '-y', 
        '-i', target_path, 
        '-vf', f"delogo=x={x}:y={y}:w={w}:h={h}", 
        '-c:a', 'copy', 
        output_name
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f"\n[SUCCESS] Watermark successfully removed!")
        print(f"Saved at: {output_name}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Engine failed during delogo processing: {e}")

if __name__ == "__main__":
    test_file = input("Enter the movie file path: ").strip().replace('"', '')
    run_delogo_workflow(test_file)

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.watermark_remover import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (watermark_remover.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'watermark_remover.py', is a core component of the Onyx Engine. It is
#    responsible for encapsulating specific FFmpeg processing logic, UI handling,
#    or filesystem operations to maintain the decoupled architecture.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    This module abstracts complex command-line operations into simple Python
#    methods. It parses inputs, constructs subprocess arrays, and handles 
#    errors gracefully without crashing the main application thread.
#
# 2. KEY FEATURES:
#    - Error Resiliency: Wraps execution in try-except blocks.
#    - Asynchronous Ready: Designed to be called from QThreads to prevent UI blocking.
#    - Clean Code: Follows strict separation of concerns.
#
# 3. APPLICATIONS:
#    - Core backend processing for the Onyx Engine UI.
#    - Standalone CLI execution for batch scripting.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - Minimal overhead in Python. The true resource cost is determined by the
#      underlying FFmpeg/FFprobe binaries which scale with video resolution.
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - Further optimization of FFmpeg filter graphs.
#    - Enhanced error reporting to the user interface.
#
# ==============================================================================
