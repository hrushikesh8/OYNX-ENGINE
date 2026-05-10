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
        '-i', input_file, 
        '-to', str(end_time), 
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
        '-i', target_path,
        '-to', end_time,
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