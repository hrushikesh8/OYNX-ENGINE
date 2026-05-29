import os
import subprocess

def extract_scene(input_file, start_time, end_time, output_name=None):
    """
    Extracts a specific scene natively without re-encoding.
    start_time and end_time can be in seconds (e.g., '125') or HH:MM:SS (e.g., '00:02:05')
    """
    if not os.path.isfile(input_file):
        print(f"[ERROR] File not found: {input_file}")
        return

    # Auto-generate a clean output name if none is provided
    if not output_name:
        base_dir = os.path.dirname(input_file)
        ext = os.path.splitext(input_file)[1]
        base_name = os.path.basename(input_file).replace(ext, "")
        
        # Clean up the timestamp for the filename (replace colons with dashes)
        safe_start = start_time.replace(':', '-')
        output_name = os.path.join(base_dir, f"{base_name}_CLIP_{safe_start}{ext}")

    print(f"\n---> Locking onto target: {start_time} to {end_time}")
    print("---> Extracting scene natively (Zero Quality Loss)...")

    # The Architecture:
    # -ss BEFORE -i makes it fast-seek instantly to the start time
    # -to tells it exactly when to stop cutting
    # -c copy prevents re-encoding
    cmd = [
        'ffmpeg', '-y', 
        '-ss', str(start_time), 
        '-to', str(end_time), 
        '-i', input_file, 
        '-c', 'copy', 
        output_name
    ]

    try:
        # We hide the messy FFmpeg logs for a clean UI experience
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f"\n[SUCCESS] Scene extracted perfectly!")
        print(f"Saved at: {output_name}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Sniper failed to extract the clip: {e}")


def run_sniper_workflow(target_path, start_time, end_time):
    """Executes the native FFmpeg stream copy using UI parameters."""
    print("\n--- Onyx Engine: Scene Sniper Activated ---")
    
    if not os.path.isfile(target_path):
        print(f"[ERROR] Invalid file path: {target_path}")
        return

    # Generate the output file name automatically
    base_dir = os.path.dirname(target_path)
    ext = os.path.splitext(target_path)[1]
    base_name = os.path.basename(target_path).replace(ext, "")
    output_name = os.path.join(base_dir, f"{base_name}_Snipped{ext}")

    # The FFmpeg Stream Copy Command (Zero Re-encoding)
    # The Frame-Accurate Command (Fixes Pixelation)
    # The Lightning-Fast "Smart Trim" Command
    cmd = [
        'ffmpeg', '-y',
        '-ss', start_time,   # Putting this BEFORE the input forces a clean Keyframe snap
        '-to', end_time,     # Must also be BEFORE the input to act as an absolute timestamp
        '-i', target_path,
        '-c', 'copy',        # Zero re-encoding. 100% original quality.
        output_name
    ]

    try:
        print(f"---> Extracting from {start_time} to {end_time}...")
        subprocess.run(cmd, check=True)
        print(f"\n[SUCCESS] Scene Extracted Successfully!")
        print(f"Saved at: {output_name}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Engine failed during extraction: {e}")

# We remove the old `if __name__ == "__main__":` block that asked for inputs

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.scene_sniper import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (scene_sniper.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'scene_sniper.py', is a core component of the Onyx Engine. It is
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
