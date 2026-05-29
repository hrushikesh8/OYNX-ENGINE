import subprocess
import json
import os
import glob

class TrackProcessor:
    def get_track_info(self, input_path: str, stream_type: str = 'a') -> list:
        """
        Returns a list of tracks (audio or subtitle) found in the video using ffprobe.
        stream_type: 'a' for audio, 's' for subtitles.
        """
        # --- FFPROBE CONFIGURATION ---
        # Construct the FFprobe command array to strictly dump stream metadata in a JSON schema.
        # This executes without decoding the media payloads, isolating metadata indices and language tags.
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'stream=index:stream_tags=language,title',
            '-select_streams', stream_type,
            '-of', 'json',
            input_path
        ]
        try:
            output = subprocess.check_output(cmd)
            data = json.loads(output)
            return data.get('streams', [])
        except Exception as e:
            print(f"❌ Error reading tracks: {e}")
            return []

    def process_batch(self, input_path: str, track_indices: list, stream_type: str = 'a'):
        """
        Handles both single files and entire folders automatically.
        Removes all tracks of `stream_type` EXCEPT the chosen IDs.
        """
        label = "audio" if stream_type == 'a' else "subtitle"
        tasks = []
        
        # --- PATH DETECTION LOGIC ---
        # 1. Detect if the input is a directory or a single file.
        # If it's a folder, we scan recursively (glob) for common video extensions.
        if os.path.isdir(input_path):
            print(f"📂 Scanning folder for videos...")
            for ext in ['*.mkv', ['*.mp4'], ['*.avi']]:
                tasks.extend(glob.glob(os.path.join(input_path, '**', ext), recursive=True))
        elif os.path.isfile(input_path):
            tasks = [input_path]
        else:
            print("❌ Invalid path provided.")
            return False

        if not tasks:
            print("❌ No videos found.")
            return False

        print(f"🚀 Processing {len(tasks)} files...")
        print("-" * 40)
        
        success_count = 0
        
        # --- STREAM RECONSTRUCTION LOOP ---
        # 2. Loop through all detected videos and clean their tracks.
        for vid in tasks:
            print(f"   ⏳ Cleaning {label.capitalize()}: {os.path.basename(vid)}")
            out_path = os.path.splitext(vid)[0] + f"_clean_{label}.mkv"
            
            # --- THE SMART FFmpeg COMMAND ---
            # Step 1: '-map 0' initializes the mapping stack with all available streams globally.
            # Step 2: '-map -0:type' executes a negative map exclusion to purge the target stream class.
            command = [
                'ffmpeg', '-i', vid,
                '-map', '0',                   
                '-map', f'-0:{stream_type}'    
            ]
            
            # Step 3: Iteratively append exact map inclusions for the preserved stream indices.
            for idx in track_indices:
                command.extend(['-map', f'0:{stream_type}:{idx}'])
                
            # --- EXECUTION FLAGS ---
            # Bypass transcoders using '-c copy' to force a direct packet-level stream multiplexing pass.
            command.extend([
                '-c', 'copy',                  
                '-ignore_unknown',             
                '-y', out_path
            ])
            
            try:
                # Running the command silently (capture_output) to keep the terminal clean.
                subprocess.run(command, check=True, capture_output=True)
                print(f"   ✅ Saved: {os.path.basename(out_path)}")
                success_count += 1
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed: {os.path.basename(vid)}")
                print(f"      FFmpeg Error: {e.stderr.decode('utf-8')}")

        print("-" * 40)
        print(f"🎉 Batch Complete! Successfully processed {success_count}/{len(tasks)} files.")
        return success_count > 0


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
#
# 1. Import:
#    from src.processors.audio import TrackProcessor
#
# 2. Instantiate:
#    cleaner = TrackProcessor()
#
# 3. USE CASE: Clean all Audio tracks except the first one (Index 0)
#    cleaner.process_batch(
#        input_path="C:/Movies/ActionMovie.mkv", 
#        track_indices=[0], 
#        stream_type='a'
#    )
#
# Result: 
# Creates a new file 'ActionMovie_clean_audio.mkv' that only contains 
# the chosen audio track, saving space and removing language clutter.
# ==========================================


# ==============================================================================
# 🎬 FEATURE: THE MULTI-STREAM TRACK PROCESSOR (TrackProcessor)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'audio.py', and it acts as a "Surgical Tool" for your 
#    video files. Its job is to look inside a movie, identify all the different 
#    audio and subtitle tracks, and let you strip away the ones you don't need. 
#    It’s essential for cleaning up bloated movie files that have 20 different 
#    languages, allowing you to keep only the ones you actually understand.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The Track Processor uses 'ffprobe' to scan the internal metadata of a 
#    container (MKV, MP4, AVI). It allows for selective mapping—a process where 
#    only specific data packets (streams) are copied from the source file to 
#    a new destination. It supports 'Batch Processing,' meaning it can clean 
#    an entire folder of movies automatically in one go.
#
# 2. KEY FEATURES:
#    - Stream Discovery: Lists all internal tracks with their language and title.
#    - Negative Mapping: Uses FFmpeg's '-map -0:a' logic to deselect all tracks 
#      before surgically adding back only the user-approved IDs.
#    - Stream Copying (-c copy): Ensures 100% original quality is maintained 
#      with zero re-encoding time.
#    - Recursive Batching: Automatically finds all videos in sub-folders.
#
# 3. APPLICATIONS:
#    - Server Optimization: Removing 'dead weight' audio tracks to save GBs 
#      of storage across a massive movie library.
#    - Language Localization: Creating clean versions of films with only 
#      native language audio and subtitles.
#    - Stream Repair: Fixing files with 'broken' metadata or unknown codecs.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - CPU Usage: Very Low. It is a 'data-moving' task, not a 'pixel-crunching' task.
#    - Time Efficiency: Extremely Fast. It processes at the speed of your 
#      storage drive's read/write limit (usually seconds per GB).
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - Metadata Editing: Renaming track titles (e.g., changing "Track 1" to 
#      "Director Commentary") without changing the audio data.
#    - Automatic Selection: Logic to "Keep all English tracks and delete others" 
#      without requiring user ID input.
#
# ==============================================================================