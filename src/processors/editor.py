import subprocess
import os
import sys
import math
import glob
from src.processors.settings_manager import SettingsManager
from src.processors.time_machine import TimeMachine

class VideoEditor:
    def convert_to_shorts_style(self, input_path: str, output_path: str, run_id: str = None):
        """Converts Landscape to Vertical (9:16) with blur background."""
        # --- ORIGINAL FILTER LOGIC (DO NOT MODIFY) ---
        # This creates the professional "Shorts" look:
        # 1. Scales the background to fill 1080x1920 and blurs it.
        # 2. Scales the original video to fit the width.
        # 3. Overlays the sharp video on top of the blurred background.
        filter_cmd = (
            "split[a][b];"
            "[a]scale=1080:1920:force_original_aspect_ratio=increase,boxblur=20:20[bg];"
            "[b]scale=1080:-2[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )
        encoder = SettingsManager.get_video_encoder("libx264")
        command = [
            'ffmpeg', '-i', input_path,
            '-vf', filter_cmd,
            '-c:v', encoder, '-preset', 'fast', '-crf', '23',
            '-c:a', 'copy', 
            '-avoid_negative_ts', 'make_zero', # 🚀 UPGRADE: Ensures seamless sync
            '-y', output_path
        ]
        try:
            print("⏳ VidFlow Editor: Processing Shorts conversion (this may take time)...")
            subprocess.run(command, check=True, capture_output=True)
            if run_id:
                TimeMachine.log_action("Shorts Editor", run_id, "CREATE_SHORTS", input_path, output_path, op_type="CREATE")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e.stderr.decode()}")
            return False

    def split_by_time(self, input_path: str, segment_time: int, run_id: str = None):
        """Splits video into multiple chunks by seconds."""
        # --- ORIGINAL NAMING LOGIC ---
        filename = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = os.path.dirname(input_path)
        output_pattern = os.path.join(output_dir, f"{filename}_part%03d.mp4")
        
        command = [
            'ffmpeg', '-i', input_path, 
            '-map', '0:v', '-map', '0:a?',
            '-c', 'copy', '-f', 'segment',
            '-segment_time', str(segment_time), 
            '-reset_timestamps', '1',
            '-avoid_negative_ts', 'make_zero', # 🚀 UPGRADE: Perfect for re-merging
            '-y', output_pattern
        ]
        try:
            print(f"✂️  VidFlow Editor: Splitting into {segment_time}s segments...")
            subprocess.run(command, check=True, capture_output=True)
            
            if run_id:
                search_pattern = os.path.join(os.path.dirname(input_path), f"{filename}_part*.mp4")
                for generated_file in glob.glob(search_pattern):
                    TimeMachine.log_action("Shorts Editor", run_id, "SPLIT_CHUNK", input_path, generated_file, op_type="CREATE")
                    
            return True
        except subprocess.CalledProcessError:
            return False

# --- STANDALONE EXECUTION LOGIC (EXACT ORIGINAL) ---
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python editor.py <file> <mode:shorts|split> [seconds]")
        sys.exit(1)

    path = sys.argv[1]
    mode = sys.argv[2]
    editor = VideoEditor()

    if mode == "shorts":
        out = os.path.splitext(path)[0] + "_shorts.mp4"
        if editor.convert_to_shorts_style(path, out):
            print(f"✅ Created: {out}")
            
    elif mode == "split":
        if len(sys.argv) < 4:
            print("❌ Split mode requires seconds argument.")
        else:
            sec = int(sys.argv[3])
            if editor.split_by_time(path, sec):
                print("✅ Split complete.")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
#
# Option 1: Create Vertical Short (TikTok/Reels Style)
# Syntax: python src/processors/editor.py "C:\Videos\Movie.mp4" "shorts"
#
# Option 2: Split Video into 30s chunks
# Syntax: python src/processors/editor.py "C:\Videos\Movie.mp4" "split" "30"
#
# Result:
# Option 1 transforms landscape video into a professional vertical 
# layout with a blurred background. Option 2 breaks the video into 
# small parts for social media status uploads.
# ==========================================


# ==============================================================================
# 🎬 FEATURE: THE CREATIVE LAYOUT & SEGMENT ENGINE (VideoEditor)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'editor.py', and it is the "Social Media Architect" 
#    of VidFlow. It specializes in two high-value tasks: converting standard 
#    wide movies into vertical "Shorts" format with a cinematic blurred 
#    background, and auto-segmenting videos into specific time-chunks.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The Editor utilizes a complex 'filter_complex' chain. It splits the 
#    video stream into two identical paths, applies a heavy Gaussian-style 
#    box blur to one (to act as the background), and overlays the sharp 
#    original on top. This maintains the artistic integrity of the shot 
#    while fitting a vertical aspect ratio.
#
# 2. KEY FEATURES:
#    - Professional Blur Overlay: Automates the "9:16 background fill" look.
#    - Segmented Exports: Automatically numbers and names video chunks.
#    - H.264 Optimization: Uses 'libx264' with a balanced CRF of 23 to 
#      ensure the output looks sharp on phone screens.
#
# 3. APPLICATIONS:
#    - Content Creation: Turning 1080p movie scenes into viral Shorts/Reels.
#    - Social Media Automation: Preparing long videos for 30-second WhatsApp 
#      or Instagram status updates.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - "Shorts" Mode: High CPU Usage (Re-encoding and filters are heavy).
#    - "Split" Mode: Near Zero (Stream copying only).
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - Adaptive Scaling: Auto-detecting the subject's face to center 
#      the crop for the "Shorts" overlay.
#
# ==============================================================================