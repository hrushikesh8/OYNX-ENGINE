import subprocess
import os
import sys

class VideoDivider:
    def split_by_chunks(self, input_path: str, segment_time: str):
        """
        Splits video into multiple chunks (e.g., for WhatsApp Status).
        segment_time can be seconds ('30') or HH:MM:SS ('00:00:30').
        """
        filename = os.path.splitext(os.path.basename(input_path))[0]
        output_pattern = os.path.join(os.path.dirname(input_path), f"{filename}_part%03d.mp4")
        
        command = [
            'ffmpeg', '-i', input_path, 
            '-map', '0',              # ✅ FIX: Keep ALL audio and subtitle tracks
            '-c', 'copy', 
            '-f', 'segment', 
            '-segment_time', str(segment_time), 
            '-reset_timestamps', '1', 
            '-ignore_unknown',        # ✅ FIX: Safety against broken streams
            '-y', output_path
        ]
        
        try:
            print(f"✂️  Dividing into chunks of {segment_time}...")
            subprocess.run(command, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr.decode('utf-8')}")
            return False

    def split_at_intermission(self, input_path: str, split_time: str):
        """
        Splits a video into exactly two parts at the specified timestamp.
        split_time can be seconds ('3600') or HH:MM:SS ('01:00:00').
        """
        base_name, ext = os.path.splitext(os.path.basename(input_path))
        output_dir = os.path.dirname(input_path)
        
        out1 = os.path.join(output_dir, f"{base_name}_First_Half{ext}")
        out2 = os.path.join(output_dir, f"{base_name}_Second_Half{ext}")

        try:
            print(f"✂️  Creating Part 1 (Start -> {split_time})...")
            # Added -map 0 and -ignore_unknown here too
            cmd1 = ['ffmpeg', '-i', input_path, '-to', str(split_time), '-map', '0', '-c', 'copy', '-ignore_unknown', '-y', out1]
            subprocess.run(cmd1, check=True, capture_output=True)

            print(f"✂️  Creating Part 2 ({split_time} -> End)...")
            cmd2 = ['ffmpeg', '-ss', str(split_time), '-i', input_path, '-map', '0', '-c', 'copy', '-ignore_unknown', '-y', out2]
            subprocess.run(cmd2, check=True, capture_output=True)
            
            return True, out1, out2
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr.decode('utf-8')}")
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

    # Time can now be passed as a string like "01:30:00"
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
# Syntax: python src/processors/division.py <VideoPath> "chunk" <Time>
# Example: python src/processors/division.py "Movie.mp4" "chunk" 00:00:30
#
# Option 2: Split Movie at Specific Time (Intermission)
# Syntax: python src/processors/division.py <VideoPath> "cut" <Time>
# Example: python src/processors/division.py "Movie.mkv" "cut" 01:05:30
# (Splits the movie into Part 1 and Part 2 exactly at 1 hour, 5 mins, 30 secs)