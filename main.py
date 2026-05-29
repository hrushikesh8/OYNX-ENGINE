import sys
from PyQt6.QtWidgets import QApplication
import qdarktheme
from gui_main import MasterOrchestrator

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Apply global dark theme
    qdarktheme.setup_theme("dark", custom_colors={"primary": "#2D72D9"})
    
    # Launch the GUI
    window = MasterOrchestrator()
    window.show()
    
    sys.exit(app.exec())


# ==============================================================================
# LIBRARY & ARCHITECTURE EXPLANATION
# ==============================================================================
# The imports above represent the "Separation of Concerns" in the VidFlow Engine.
# Instead of cramming FFmpeg commands into this main file, we import dedicated 
# Classes (like `VideoEditor` or `AudioExtractor`) from the `src.processors` folder.
# This keeps main.py acting strictly as an 'Orchestrator' or 'Router'. It asks the 
# user what they want, and then hands the actual work off to the imported tools.
# ==============================================================================




# ==============================================================================
# 🚀 HOW TO RUN THE VIDFLOW ENGINE (EXECUTION EXAMPLES)
# ==============================================================================
#
# 1. SETUP:
#    Ensure your folder structure matches the import statements at the top.
#    /VidFlow_Project/
#      ├── main.py
#      └── src/
#           ├── utils/system.py
#           └── processors/ (division.py, editor.py, watermark.py, etc.)
#
# 2. RUN THE ENGINE:
#    Open your terminal or command prompt inside the VidFlow_Project folder.
#    Run: `python main.py`
#
# 3. WORKFLOW EXAMPLES:
#    - Example A (Mass Audio Ripping): 
#      Press '15' -> Drag a folder of downloaded music videos -> Type 'mp3'.
#      VidFlow will rip high-quality audio files from every video in that folder.
#    
#    - Example B (Watermarking a Library):
#      Press '11' -> Drag a folder of .mp4s -> Drag your logo.png -> Type 'br'.
#      VidFlow will burn your logo into the bottom right of every video.
#
# ==============================================================================

"""
-----------------------------------------------------------------------
                           FEATURES EXPLANATION (18 MODULES)
-----------------------------------------------------------------------

FORMATS & TRACKS
1.  Format Converter: Changes video containers (e.g., MKV to MP4) without 
    losing quality. Automatically detects if you input a single file or a folder.
2.  Track Cleaner (Audio): Scans a video for all audio languages/dubs. Lets 
    you enter the IDs of the ones you want to keep and purges the rest to save space.
3.  Track Cleaner (Subtitles): Scans a video for subtitle tracks. Purges 
    unwanted languages while keeping your selected IDs perfectly synced.

MERGE & STITCH
4.  Stream Merger (Audio): Takes a silent/separate video file and an audio 
    file (WAV/MP3) and muxes them together in perfect timeline sync.
5.  Stream Merger (Subtitles): Softcodes an external .srt or .ass subtitle 
    file into a video container so it can be toggled on/off in media players.
6.  Video Stitcher: Uses the 'concat demuxer' to take multiple video parts 
    (Part 1, Part 2) and instantly join them into one continuous movie.

EDIT & DIVIDE
7.  Divider (Intermission): Slices a massive movie perfectly in half (or at 
    any specific timestamp) without re-encoding, creating two playable files.
8.  Divider (Chunks): Automatically slices a long video into perfectly even 
    chunks (e.g., 30-second segments) for WhatsApp status or social media.
9.  Editor (Specific Segments): Surgically extracts a specific highlight 
    or scene from a movie without losing original 4K/HDR quality.
10. Editor (9:16 Shorts): Transforms standard widescreen movies into vertical 
    TikTok/Reels format by applying a professional blurred-background overlay.

BRANDING & EXPORT
11. Watermarker: Burns a custom PNG logo into the video frames. Includes 
    smart positioning (br, tl, center) and can batch-process entire folders.
12. GIF Maker: Converts video segments into loopable GIFs using a dual-pass 
    palette generation system to ensure cinematic, high-quality colors.
13. Compressor: Scans a folder for videos over a specific size (e.g., 1.5GB) 
    and intelligently compresses their audio tracks to reduce server footprint.

EXTRACTION (THE HARVESTER)
14. Extractor (Single): Rips the audio from a video file to MP3, WAV, or 
    copies the original lossless stream instantly.
15. Extractor (Mass Harvester): Scans a massive folder recursively and rips 
    the audio from every single video it finds. Perfect for music libraries.
16. Extractor (Targeted): Allows you to extract specific embedded tracks 
    (like Track 2 for Telugu or Track 3 for Hindi) directly to an audio file.

AI RESTORATION
17. Remaster (Standard): Enhances older footage by reducing noise and upscaling.
18. Remaster (Theatrical AI): Uses deep-learning (requires RTX GPU) to restore 
    1980s-2005 footage. Includes a 2-minute "Sample Check" before committing 
    to a 12-hour full-movie restoration.

-----------------------------------------------------------------------
"""

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.main import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (main.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'main.py', is a core component of the Onyx Engine. It is
#    responsible for encapsulating specific FFmpeg processing logic, UI handling,
#    or filesystem operations to maintain the decoupled architecture.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    This module abstracts complex command-line operations into simple Python
#    methods. It parses inputs, constructs subprocess arrays, and handles 
#    errors gracefully without crashing the main application thread.
#
# 2. KEY FEATURES:
#    - Error Resiliency: Wraps execution in try-except blocks.
#    - Asynchronous Ready: Designed to be called from QThreads to prevent UI blocking.
#    - Clean Code: Follows strict separation of concerns.
#
# 3. APPLICATIONS:
#    - Core backend processing for the Onyx Engine UI.
#    - Standalone CLI execution for batch scripting.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - Minimal overhead in Python. The true resource cost is determined by the
#      underlying FFmpeg/FFprobe binaries which scale with video resolution.
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - Further optimization of FFmpeg filter graphs.
#    - Enhanced error reporting to the user interface.
#
# ==============================================================================
