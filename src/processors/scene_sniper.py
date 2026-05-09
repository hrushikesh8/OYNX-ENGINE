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

def run_sniper_workflow(target_path):
    print("\n--- VidFlow: Scene Sniper ---")
    
    if os.path.isdir(target_path):
        print("[INFO] Please provide a direct path to a specific movie FILE, not a folder.")
        return

    print("Format examples: '125' (seconds) OR '01:15:30' (HH:MM:SS)")
    start_time = input("Enter START time: ").strip()
    end_time = input("Enter END time: ").strip()

    if start_time and end_time:
        extract_scene(target_path, start_time, end_time)
    else:
        print("[ERROR] You must provide both a start and end time.")

if __name__ == "__main__":
    test_file = input("Enter the movie file path: ").strip().replace('"', '')
    run_sniper_workflow(test_file)