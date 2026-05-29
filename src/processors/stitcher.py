import subprocess
import os
import sys
import tempfile

class VideoStitcher:
    def concat_videos(self, video_list: list, output_path: str):
        """
        Joins videos using the concat demuxer (Instant join).
        Requirement: Matching resolution/codecs.
        """
        if not video_list:
            return False

        # Use a unique temp file to prevent conflicts during parallel processing
        fd, list_file_path = tempfile.mkstemp(suffix=".txt", prefix="onyx_stitch_")
        
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                for vid in video_list:
                    # Ensure absolute paths for FFmpeg -safe 0
                    abs_path = os.path.abspath(vid).replace("'", "'\\''")
                    f.write(f"file '{abs_path}'\n")

            # Construct the Concat Demuxer instruction array natively.
            # -f concat: Processes inputs synchronously at the packet level.
            # -safe 0: Overrides FFmpeg security policies to permit absolute OS path addressing.
            command = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', list_file_path,
                '-c', 'copy', 
                '-avoid_negative_ts', 'make_zero', # Mitigates PTS/DTS desyncs at join boundaries.
                '-y', output_path
            ]

            print(f"🔗 Onyx Stitcher: Joining {len(video_list)} segments...")
            subprocess.run(command, check=True, capture_output=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg Stitch Error: {e.stderr.decode()}")
            return False
        finally:
            # Always clean up the temp file
            if os.path.exists(list_file_path):
                os.remove(list_file_path)

if __name__ == "__main__":
    # Your original CLI logic remains compatible
    if len(sys.argv) < 3:
        print("Usage: python stitcher.py <output_file> <input_video_1> ...")
        sys.exit(1)

    stitcher = VideoStitcher()
    if stitcher.concat_videos(sys.argv[2:], sys.argv[1]):
        print(f"✅ Success: {sys.argv[1]}")

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