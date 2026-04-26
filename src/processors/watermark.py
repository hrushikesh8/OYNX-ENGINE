import subprocess
import os
import sys

class Watermarker:
    def add_image_watermark(self, video_path: str, image_path: str, output_path: str, position="br"):
        """
        Overlays an image (logo) onto the video.
        User-selectable positions: 
        'tl', 'tr', 'bl', 'br', 'center'
        """
        
        # --- THE CONTROL CENTER (Coordinate Logic) ---
        # main_w/main_h = Video size | overlay_w/overlay_h = Logo size
        # We use a 10-pixel offset to keep the logo slightly away from the absolute edge.
        coords = {
            "tl": "10:10",                                   # Top-Left
            "tr": "main_w-overlay_w-10:10",                 # Top-Right
            "bl": "10:main_h-overlay_h-10",                 # Bottom-Left
            "br": "main_w-overlay_w-10:main_h-overlay_h-10",# Bottom-Right
            "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2"
        }
        
        # Logic: If the user types a custom or wrong position, it defaults to 'br'
        overlay_setting = coords.get(position.lower(), coords["br"])

        # --- FFmpeg EXECUTION ---
        command = [
            'ffmpeg', '-i', video_path, '-i', image_path,
            '-filter_complex', f"overlay={overlay_setting}",
            '-c:a', 'copy',                 # Original audio stays high-quality
            '-avoid_negative_ts', 'make_zero', # 🚀 SEAMLESS JOIN UPGRADE
            '-y', output_path
        ]

        try:
            print(f"💧 VidFlow Branding: Applying watermark to {os.path.basename(video_path)}...")
            print(f"🎮 User Control: Positioning set to '{position.upper()}'")
            # Re-encoding is necessary to burn the pixels into the video
            subprocess.run(command, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error during watermarking: {e.stderr.decode()}")
            return False

# --- STANDALONE EXECUTION LOGIC ---
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("❌ VidFlow Error: Missing arguments.")
        print("-" * 30)
        print("Usage: python watermark.py <video_path> <logo_path> <position>")
        print("Available Positions:")
        print("  tl - Top Left")
        print("  tr - Top Right")
        print("  bl - Bottom Left")
        print("  br - Bottom Right (Recommended)")
        print("  center - Center Overlay")
        print("-" * 30)
        sys.exit(1)

    vid = sys.argv[1]
    img = sys.argv[2]
    pos = sys.argv[3] # The user's choice
    
    # Standardized output naming convention
    out = os.path.splitext(vid)[0] + "_branded.mp4"
    
    wm = Watermarker()
    if wm.add_image_watermark(vid, img, out, pos):
        print(f"✅ Branding Complete: {out}")
    def remove_watermark(self, video_path: str, output_path: str, x: int, y: int, w: int, h: int):
        """
        🚀 NEW: Removes a watermark using AI-style in-painting (delogo).
        Requires exact coordinates (x, y) and dimensions (width, height) of the logo.
        """
        # --- DELOGO COMMAND ---
        # -vf delogo=x:y:w:h : Targets a specific box and blurs the surrounding pixels over it.
        command = [
            'ffmpeg', '-i', video_path,
            '-vf', f"delogo=x={x}:y={y}:w={w}:h={h}",
            '-c:a', 'copy',
            '-avoid_negative_ts', 'make_zero',
            '-y', output_path
        ]

        try:
            print(f"🧹 VidFlow Branding: Scrubbing watermark from {os.path.basename(video_path)}...")
            subprocess.run(command, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error during watermark removal: {e.stderr.decode()}")
            return False
# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
#
# Option 1: Standard Bottom-Right (Most Common)
# python src/processors/watermark.py "Movie.mp4" "logo.png" "br"
#
# Option 2: Top-Left (For specific branding styles)
# python src/processors/watermark.py "Movie.mp4" "logo.png" "tl"
#
# Result: 
# Places the logo exactly where the user chooses. The code calculates 
# the dimensions automatically so the logo never goes "off-screen" 
# regardless of the video resolution.
# ==========================================


# ==============================================================================
# 🎬 FEATURE: THE BRANDING & IDENTITY ENGINE (Watermarker)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'watermark.py', and its job is "Identity." It allows 
#    the user to burn a logo into a video. This is a foundational tool for 
#    your future cloud farm, ensuring every piece of content that leaves 
#    your server is marked with the 'VidFlow' brand.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The Watermarker uses a complex overlay filter. By referencing 'main_w' 
#    and 'overlay_w', it creates a relative positioning system. This means 
#    the logo will appear in the same relative corner whether the video 
#    is 4K or 480p, without the user needing to calculate pixels.
#
# 2. KEY FEATURES:
#    - User-Driven Positioning: 5 distinct presets for full layout control.
#    - Audio Fidelity: Uses '-c:a copy' to ensure that while the video is 
#      re-encoded for branding, the sound remains untouched and perfect.
#    - Seamless Join Ready: Includes 'make_zero' logic to ensure branded 
#      clips can be clubbed together without sync issues.
#
# 3. APPLICATIONS:
#    - Ownership Branding: Preventing content theft on public servers.
#    - Theatrical Labeling: Adding "VidFlow Originals" logos to movies.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - CPU/GPU: High. Re-encoding every frame to burn the logo is 
#      computationally expensive.
#    - Speed: Average. Typically processes at 0.5x to 2x real-time speed.
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - AI Watermark Removal: Adding a "delogo" feature for third-party videos.
#    - Opacity Slider: Allowing the user to choose how transparent the logo is.
#
# ==============================================================================