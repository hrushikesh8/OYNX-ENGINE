import subprocess
import os
import sys

class VideoStitcher:
    def concat_videos(self, video_list: list, output_path: str):
        """
        Joins multiple video files into one using the FFmpeg 'concat demuxer'.
        Requirements: All videos must have the same codec/resolution.
        """
        if not video_list:
            return False

        # 1. Create a temporary text file listing all videos
        # Format: file 'path/to/video.mp4'
        list_file_path = "temp_stitch_list.txt"
        with open(list_file_path, "w", encoding='utf-8') as f:
            for vid in video_list:
                # FFmpeg requires paths to be escaped strictly (ORIGINAL LOGIC PRESERVED)
                safe_path = vid.replace("'", "'\\''") 
                f.write(f"file '{safe_path}'\n")

        # 2. Run FFmpeg concat command
        # -f concat: Use the concat format
        # -safe 0: Allow unsafe file paths (absolute paths)
        # -c copy: No re-encoding (Instant join)
        # -avoid_negative_ts make_zero: 🚀 SEAMLESS UPGRADE for perfect server playback
        command = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', list_file_path,
            '-c', 'copy', 
            '-avoid_negative_ts', 'make_zero',
            '-y', output_path
        ]

        try:
            print(f"🔗 VidFlow Stitcher: Stitching {len(video_list)} files...")
            subprocess.run(command, check=True, capture_output=True)
            
            # Cleanup temp file
            os.remove(list_file_path)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e.stderr.decode()}")
            if os.path.exists(list_file_path):
                os.remove(list_file_path)
            return False

# --- STANDALONE EXECUTION LOGIC (EXACT ORIGINAL) ---
if __name__ == "__main__":
    # Usage: python stitcher.py output.mp4 video1.mp4 video2.mp4 video3.mp4 ...
    if len(sys.argv) < 3:
        print("Usage: python stitcher.py <output_file> <input_video_1> <input_video_2> ...")
        sys.exit(1)

    output_file = sys.argv[1]
    input_videos = sys.argv[2:]

    stitcher = VideoStitcher()
    if stitcher.concat_videos(input_videos, output_file):
        print(f"✅ Successfully stitched into: {output_file}")
    else:
        print("❌ Failed to stitch videos. Ensure they have matching formats.")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
#
# Syntax: python src/processors/stitcher.py <Output> <Input1> <Input2> ...
#
# Example Command:
# python src/processors/stitcher.py "FullMovie.mp4" "Part1.mp4" "Part2.mp4"
#
# Note on Speed: Because this uses 'stream copying' (-c copy), there 
# is no need for 'fast' or 'medium' presets. The stitching process 
# is mathematically lossless and happens instantly.
# ==========================================


# ==============================================================================
# 🎬 FEATURE: THE HIGH-SPEED STITCHER (VideoStitcher)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'stitcher.py', and its job is "Reconstruction." 
#    If 'division.py' is the tool that breaks your massive movies into 
#    First_Half and Second_Half, this is the tool that clubs them back 
#    together for your Cloud Farm seamlessly, as if they were never cut.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The Stitcher uses FFmpeg's 'concat demuxer' (concatenation). Unlike 
#    standard merging, which puts audio and video side-by-side, concat 
#    puts files end-to-end sequentially. It writes a temporary text file 
#    with strict path escaping to feed the exact sequence to the engine.
#
# 2. KEY FEATURES:
#    - Strict Path Escaping: Safely handles folder names that contain spaces 
#      or apostrophes (e.g., "Director's Cut").
#    - Seamless Join Ready: Upgraded with 'make_zero' timestamp logic so 
#      the transition between Part 1 and Part 2 doesn't drop a single frame.
#    - Instant Execution: Uses '-c copy' to bypass re-encoding, joining 
#      gigabytes of video in mere seconds.
#
# 3. APPLICATIONS:
#    - Server Farm Assembly: Rebuilding chunked files into full-length movies.
#    - Series Compilation: Combining opening credits, an episode, and 
#      closing credits into a single broadcast file.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - CPU/GPU Usage: Near 0%.
#    - Speed: Instant (limited only by hard drive write speed).
#
# ==============================================================================