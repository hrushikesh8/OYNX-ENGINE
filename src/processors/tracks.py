import subprocess
import json
import os
import glob
import sys

class TrackProcessor:
    def get_track_info(self, input_path: str, stream_type: str = 'a') -> list:
        """
        Returns a list of tracks (audio or subtitle) found in the video using ffprobe.
        stream_type: 'a' for audio, 's' for subtitles.
        """
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
        """
        Handles both single files and entire folders automatically.
        Removes all tracks of `stream_type` EXCEPT the chosen IDs.
        """
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
        
        # 2. Loop through all videos and clean their tracks
        for vid in tasks:
            print(f"   ⏳ Cleaning {label.capitalize()}: {os.path.basename(vid)}")
            out_path = os.path.splitext(vid)[0] + f"_clean_{label}.mkv"
            
            # THE SMART FFmpeg COMMAND
            command = [
                'ffmpeg', '-i', vid,
                '-map', '0',                   # Step 1: Keep EVERYTHING (Video, Audio, Subs)
                '-map', f'-0:{stream_type}'    # Step 2: Deselect ALL tracks of the chosen type ('a' or 's')
            ]
            
            # Step 3: Add back ONLY the specific track IDs the user chose
            for idx in track_indices:
                command.extend(['-map', f'0:{stream_type}:{idx}'])
                
            command.extend([
                '-c', 'copy',                  # No re-encoding (Fast)
                '-ignore_unknown',             # Safety net against broken "codec: none" streams!
                '-y', out_path
            ])
            
            try:
                subprocess.run(command, check=True, capture_output=True)
                print(f"   ✅ Saved: {os.path.basename(out_path)}")
                success_count += 1
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed: {os.path.basename(vid)}")
                print(f"      FFmpeg Error: {e.stderr.decode('utf-8')}")

        print("-" * 40)
        print(f"🎉 Batch Complete! Successfully processed {success_count}/{len(tasks)} files.")
        return success_count > 0

# --- STANDALONE EXECUTION LOGIC ---
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("❌ Error: Missing arguments.")
        print("Usage: python tracks.py <VideoPath> <Mode> <TrackIDs>")
        sys.exit(1)

    input_arg = sys.argv[1]
    mode_arg = sys.argv[2].lower()
    
    if mode_arg not in ['a', 's']:
        print("❌ Error: Mode must be 'a' (Audio) or 's' (Subtitles).")
        sys.exit(1)

    try:
        # Convert "0,2" into a list of integers: [0, 2]
        indices_arg = [int(x.strip()) for x in sys.argv[3].split(',')]
    except ValueError:
        print("❌ Error: TrackIDs must be comma-separated numbers (e.g., 0,2).")
        sys.exit(1)

    processor = TrackProcessor()
    processor.process_batch(input_arg, indices_arg, mode_arg)

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