import subprocess
import os
import sys
import glob
from src.processors.settings_manager import SettingsManager
from src.processors.time_machine import TimeMachine

class VideoDivider:
    def split_by_chunks(self, input_path: str, segment_time: str, run_id: str = None):
        """
        Splits video into multiple equal chunks (e.g., for WhatsApp Status).
        segment_time can be seconds ('30') or HH:MM:SS ('00:00:30').
        """
        # --- FILENAME & PATH LOGIC ---
        # Extracts original name and sets a pattern like 'Movie_part001.mp4'
        filename = os.path.splitext(os.path.basename(input_path))[0]
        output_pattern = os.path.join(os.path.dirname(input_path), f"{filename}_part%03d.mp4")
        
        # --- FFmpeg SEGMENT COMMAND ---
        # -map 0: Keeps all Audio and Subtitles.
        # -c copy: Zero quality loss.
        # -reset_timestamps 1: Essential for standalone playback of chunks.
        # -avoid_negative_ts make_zero: UPGRADE - Ensures chunks join perfectly later.
        # 🚀 UPGRADE: Conditionally apply subtitle safeguard
        maps = ['-map', '0:v', '-map', '0:a?'] if SettingsManager.should_safeguard_subtitles() else ['-map', '0']
        
        command = [
            'ffmpeg', '-i', input_path, 
        ] + maps + [
            '-c', 'copy', 
            '-f', 'segment', 
            '-segment_time', str(segment_time), 
            '-reset_timestamps', '1', 
            '-avoid_negative_ts', 'make_zero', 
            '-ignore_unknown', 
            '-y', output_pattern
        ]
        
        try:
            print(f"✂️  VidFlow Division: Dividing into chunks of {segment_time}...")
            subprocess.run(command, check=True, capture_output=True)
            
            # ---> TIME MACHINE LOGGING <---
            if run_id:
                search_pattern = os.path.join(os.path.dirname(input_path), f"{filename}_part*.mp4")
                for generated_file in glob.glob(search_pattern):
                    TimeMachine.log_action("Video Divider", run_id, "SPLIT_CHUNK", input_path, generated_file, op_type="CREATE")
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e.stderr.decode('utf-8')}")
            return False

    def split_at_intermission(self, input_path: str, split_time: str, run_id: str = None):
        """
        Splits a video into exactly two parts at the specified timestamp.
        split_time can be seconds ('3600') or HH:MM:SS ('01:00:00').
        """
        # --- NAMING & DIRECTORY LOGIC ---
        # Preserves the directory and creates specific "First_Half" and "Second_Half" files.
        base_name, ext = os.path.splitext(os.path.basename(input_path))
        output_dir = os.path.dirname(input_path)
        
        out1 = os.path.join(output_dir, f"{base_name}_First_Half{ext}")
        out2 = os.path.join(output_dir, f"{base_name}_Second_Half{ext}")

        try:
            # --- PART 1 GENERATION ---
            print(f"✂️  Generating Part 1 (Start -> {split_time})...")
            # Uses -to for precise ending point.
            # 🚀 UPGRADE: Conditionally apply subtitle safeguard
            maps = ['-map', '0:v', '-map', '0:a?'] if SettingsManager.should_safeguard_subtitles() else ['-map', '0']
            
            cmd1 = [
                'ffmpeg', '-i', input_path, 
                '-to', str(split_time), 
            ] + maps + [
                '-c', 'copy', 
                '-avoid_negative_ts', 'make_zero', 
                '-ignore_unknown', '-y', out1
            ]
            subprocess.run(cmd1, check=True, capture_output=True)

            # --- PART 2 GENERATION ---
            print(f"✂️  Generating Part 2 ({split_time} -> End)...")
            # Uses -ss BEFORE -i for the fastest seeking to the second half.
            cmd2 = [
                'ffmpeg', '-ss', str(split_time), 
                '-i', input_path, 
            ] + maps + [
                '-c', 'copy', 
                '-avoid_negative_ts', 'make_zero', 
                '-ignore_unknown', '-y', out2
            ]
            subprocess.run(cmd2, check=True, capture_output=True)
            
            # ---> TIME MACHINE LOGGING <---
            if run_id:
                TimeMachine.log_action("Video Divider", run_id, "SPLIT_INTERMISSION_P1", input_path, out1, op_type="CREATE")
                TimeMachine.log_action("Video Divider", run_id, "SPLIT_INTERMISSION_P2", input_path, out2, op_type="CREATE")
            
            return True, out1, out2
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e.stderr.decode('utf-8')}")
            return False, None, None

# --- STANDALONE EXECUTION LOGIC ---
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("❌ Error: Missing arguments.")
        print("Usage: python division.py <file> <mode:chunk|cut> [time]")
        sys.exit(1)

    path = sys.argv[1]
    mode = sys.argv[2]
    divider = VideoDivider()

    # Time can be seconds like "3600" or HH:MM:SS like "01:00:00"
    time_val = sys.argv[3] if len(sys.argv) > 3 else "30"

    if mode == "chunk":
        if divider.split_by_chunks(path, time_val):
            print("✅ Chunk division complete.")

    elif mode == "cut":
        success, p1, p2 = divider.split_at_intermission(path, time_val)
        if success:
            print(f"✅ Cut Complete:\n   Part 1: {p1}\n   Part 2: {p2}")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
#
# Option 1: Split into Chunks (e.g., for WhatsApp Status)
# Syntax:  python src/processors/division.py <VideoPath> "chunk" <Time>
# Example: python src/processors/division.py "Movie.mp4" "chunk" 00:00:30
#
# Option 2: Split Movie at Specific Time (Intermission)
# Syntax:  python src/processors/division.py <VideoPath> "cut" <Time>
# Example: python src/processors/division.py "Movie.mkv" "cut" 01:05:30
# (Splits the movie into Part 1 and Part 2 exactly at 1 hour, 5 mins, 30 secs)
#
# Result: 
# Perfectly organized files. Option 2 renames them to "First_Half" and 
# "Second_Half" for easy identification on your cloud server.
# ==========================================


# ==============================================================================
# 🎬 FEATURE: THE PRECISION VIDEO SPLITTER (VideoDivider)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'division.py', and its job is "Segmentation." 
#    It is a specialized tool for breaking long media into manageable parts. 
#    Whether you are prepping 30-second clips for social media or splitting 
#    a 3-hour epic into two halves for your server, this engine ensures 
#    the cut is clean and the file names are perfectly organized.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The Division Engine uses FFmpeg's 'segment' and 'seeking' logic. It is 
#    optimized for 'Stream Copying' mode, meaning it doesn't process 
#    individual pixels—it cuts the data stream at the nearest Keyframe, 
#    making the process instant and 100% lossless.
#
# 2. KEY FEATURES:
#    - Seamless Joining Support: Uses '-avoid_negative_ts' so that Part 1 
#      and Part 2 can be clubbed back together later without glitches.
#    - Timestamp Precision: Supports both raw seconds and HH:MM:SS formats.
#    - Automatic Naming: Renames files as "First_Half" and "Second_Half" 
#      automatically to keep your library organized.
#    - Full Stream Preservation: Keeps all audio and subtitle tracks intact.
#
# 3. APPLICATIONS:
#    - Cloud Server Prep: Splitting large files for easier storage and 
#      continuous playback on your future server farm.
#    - Status/Reel Creation: Automating the 30-second chunking process.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - Speed: Instant. Processes 4K movies in seconds.
#    - CPU/GPU: Near Zero (Data copying only).
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - Auto-Intermission: Linking with 'intel.py' to find the best 
#      dramatic scene cut to split the movie automatically.
#
# ==============================================================================