import subprocess
import json
import os
import glob
import sys

class TrackProcessor:
    """
    🎬 FEATURES 2 & 3: TRACK CLEANER (Original Logic Intact)
    Handles the intelligent selection and purging of Audio/Subtitle streams.
    """
    def get_track_info(self, input_path: str, stream_type: str = 'a') -> list:
        """Returns a list of tracks found in the video using ffprobe."""
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
            print(f"Error reading tracks: {e}")
            return []

    def process_batch(self, input_path: str, track_indices: list, stream_type: str = 'a'):
        """Handles both single files and folders. Removes chosen type EXCEPT chosen IDs."""
        label = "audio" if stream_type == 'a' else "subtitle"
        tasks = []
        
        # 1. Detect if it's a folder or a single file
        if os.path.isdir(input_path):
            print(f"📂 Scanning folder for videos...")
            for ext in ['*.mkv', '*.mp4', '*.avi']:
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
        
        for vid in tasks:
            print(f"   ⏳ Cleaning {label.capitalize()}: {os.path.basename(vid)}")
            out_path = os.path.splitext(vid)[0] + f"_clean_{label}.mkv"
            
            # --- DYNAMIC STREAM ROUTING ---
            # -map 0: Globally includes all source streams.
            # -map -0:{stream_type}: A negative map assertion to explicitly reject the target codec class.
            command = [
                'ffmpeg', '-i', vid,
                '-map', '0',                          
                '-map', f'-0:{stream_type}'           
            ]
            
            # Step 3: Add back ONLY the specific track IDs
            for idx in track_indices:
                # We use the provided indices from the UI checkboxes
                command.extend(['-map', f'0:{stream_type}:{idx}'])
                
            command.extend([
                '-c', 'copy',                         # Packet-level stream copy (Zero decoding).
                '-ignore_unknown',                    # Suppresses abortions caused by esoteric metadata headers.
                '-avoid_negative_ts', 'make_zero',    # Shifts PTS/DTS vectors to origin (0) to resolve container desync.
                '-y', out_path
            ])
            
            try:
                subprocess.run(command, check=True, capture_output=True)
                print(f"   ✅ Saved: {os.path.basename(out_path)}")
                success_count += 1
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed: {os.path.basename(vid)}")

        print("-" * 40)
        return success_count > 0

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
#
# Syntax: python src/processors/tracks.py <VideoPath> <Mode> <TrackIDs>
#
# Mode: 'a' for Audio, 's' for Subtitles
# TrackIDs: The index numbers of tracks to KEEP (separated by comma)
#
# Example Command:
# python src/processors/tracks.py "C:\Movies\Avatar.mkv" "a" "0,2"
#
# (This keeps Audio Track 0 and 2, removes the rest)
#
# BATCH FOLDER EXAMPLE:
# python src/processors/tracks.py "C:\Movies\Season1" "s" "0"
#
# (This looks at every video in the folder and removes all subtitles EXCEPT Track 0)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: THE MULTI-STREAM TRACK CLEANER (TrackProcessor)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'tracks.py', and it acts as a "Surgical Tool" for your 
#    video files. Its job is to identify all the different audio and subtitle 
#    tracks inside a container, and let you strip away the ones you don't need. 
#    It’s essential for cleaning up bloated movie files that have 20 different 
#    languages, allowing you to keep only the ones you actually want on your server.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The Track Processor uses 'ffprobe' to scan the internal metadata. It uses 
#    Negative Mapping ('-map -0:a') to deselect all tracks before surgically 
#    adding back only the user-approved IDs. It supports 'Batch Processing,' 
#    meaning it can clean an entire folder of movies automatically in one go.
#
# 2. KEY FEATURES:
#    - Stream Copying (-c copy): Ensures 100% original quality is maintained 
#      with zero re-encoding time.
#    - Recursive Batching: Automatically finds all videos in sub-folders.
#    - Timeline Synchronization: Includes '-avoid_negative_ts' to ensure the 
#      cleaned files don't suffer from audio sync issues.
#
# 3. APPLICATIONS:
#    - Server Optimization: Removing 'dead weight' audio tracks to save GBs 
#      of storage across a massive movie library.
#    - Language Localization: Creating clean versions of films with only 
#      native language audio and subtitles.
#
# ==============================================================================