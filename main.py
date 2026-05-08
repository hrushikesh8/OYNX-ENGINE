import os
import glob
import sys
import time
from src.utils.system import SystemUtils
from src.processors.formats import FormatMapper
from src.processors.tracks import TrackProcessor
from src.processors.merger import StreamMerger
from src.processors.compressor import VideoCompressor
from src.processors.editor import VideoEditor
from src.processors.division import VideoDivider
from src.processors.stitcher import VideoStitcher
from src.processors.watermark import Watermarker
from src.processors.gif_maker import GifMaker
from src.processors.remaster import VideoRemaster
from src.processors.extractor import AudioExtractor
from src.processors.archiver import FolderArchiver
from src.processors.remaster_service import RemasterService
from src.processors.unarchiver import EnterpriseUnarchiver
# Import the standalone Seamless Suture module (Feature 22)
import seamless_suture


# ==============================================================================
# LIBRARY & ARCHITECTURE EXPLANATION
# ==============================================================================
# The imports above represent the "Separation of Concerns" in the VidFlow Engine.
# Instead of cramming FFmpeg commands into this main file, we import dedicated 
# Classes (like `VideoEditor` or `AudioExtractor`) from the `src.processors` folder.
# This keeps main.py acting strictly as an 'Orchestrator' or 'Router'. It asks the 
# user what they want, and then hands the actual work off to the imported tools.
# ==============================================================================


def scan_folder(folder_path, extensions):
    """
    Helper Function: Recursively finds files matching extensions in a folder.
    This enables the 'Batch Processing' logic across the entire engine.
    """
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(glob.escape(folder_path), '**', f'*{ext}'), recursive=True))
    return files

def get_path(prompt="Enter file or folder path: "):
    """
    Helper Function: Smart helper to strip quotes from drag-and-dropped paths.
    Windows adds quotes when you drag a file into the terminal; this removes them.
    """
    return input(prompt).strip('"').strip("'")

def main():
    # Pre-flight check: Ensure FFmpeg is installed before showing the menu
    if not SystemUtils.check_ffmpeg_availability():
        print("❌ CRITICAL: FFmpeg not found. Please install it and add to PATH.")
        return

    # The Master Loop: Keeps the application running until the user types '0'
    while True:
        print("\n" + "="*55)
        print(" 🎬 VIDFLOW ENGINE v1.5 (MASTER ORCHESTRATOR) ")
        print("="*55)
        print(" --- FORMATS & TRACKS ---")
        print("  1.  Format Converter (Smart Single/Batch)")
        print("  2.  Track Cleaner: Audio (Remove unwanted dubs)")
        print("  3.  Track Cleaner: Subtitles (Purge extra subs)")
        print(" --- MERGE & STITCH ---")
        print("  4.  Stream Merger: Audio + Video Sync")
        print("  5.  Stream Merger: Mux/Embed Subtitles")
        print("  6.  Video Stitcher: Concat Parts Seamlessly")
        print(" --- EDIT & DIVIDE ---")
        print("  7.  Divider: Theatrical Intermission (2-Parts)")
        print("  8.  Divider: Chunk for WhatsApp/Reels (30s)")
        print("  9.  Editor: Split by Specific Time Segments")
        print(" 10.  Editor: Convert to 9:16 Shorts (Blur BG)")
        print(" --- BRANDING & EXPORT ---")
        print(" 11.  Watermarker: Burn Logo (With Position/Batch)")
        print(" 12.  Watermarker: Remove Logo (In-painting/Delogo)") # 🚀 NEW
        print(" 13.  GIF Maker: High-Quality Palette Engine")
        print(" 14.  Compressor: Smart Size Reduction")
        print(" --- EXTRACTION (HARVESTER) ---")
        print(" 15.  Extractor: Single Audio Rip")
        print(" 16.  Extractor: Mass Harvester (Folder Batch Rip)")
        print(" 17.  Extractor: Target Specific Track ID")
        print(" --- AI RESTORATION & ARCHIVAL ---")
        print(" 18.  Remaster: Standard Enhancement")
        print(" 19.  Remaster: Theatrical AI Restoration (RTX)")
        print(" 20.  Archiver: Project Packaging & Cleanup") # 🚀 NEW
        print(" 21.  Unarchiver: Project Unpackaging") # 🚀 NEW
        # Feature 22: Native Stream Concat for Split Movies
        print("22. Seamless Suture (Merge Split MKV/MP4 parts instantly)")
        print("  0.  Exit VidFlow")
        print("="*55)

        choice = input("Select an Engine (0-21): ").strip()
        
        if choice == '0':
            print("\nShutting down VidFlow... Get some rest!")
            sys.exit(0)

        # Global success flag used for clean logging at the end of the loop
        success = False

        # ---------------------------------------------------------
        # 1. FORMAT CONVERTER (SMART DETECTION)
        # ---------------------------------------------------------
        # Changes the container of a video (e.g., MKV to MP4).
        # We use `os.path.isdir` to detect if the user provided a folder.
        # If it's a folder, we batch convert everything inside it automatically.
        if choice == "1":
            target_path = get_path()
            fmt = input("Target format (mp4/mkv/avi): ").lower()
            processor = FormatMapper()
            
            if os.path.isdir(target_path):
                # Batch Mode: Create an output folder inside the source directory
                out_dir = os.path.join(target_path, "converted")
                processor.process_input(target_path, out_dir, fmt)
                success = True
            elif os.path.isfile(target_path):
                # Single Mode: Create an output folder next to the source file
                out_dir = os.path.join(os.path.dirname(target_path), "converted")
                processor.process_input(target_path, out_dir, fmt)
                success = True
            else:
                print("❌ Path not found.")

        # ---------------------------------------------------------
        # 2 & 3. TRACK CLEANER (AUDIO / SUBTITLES)
        # ---------------------------------------------------------
        # Purges unwanted languages from a movie file to save server space.
        # It scans the first file it finds to show the user a list of available tracks.
        elif choice in ["2", "3"]:
            target_path = get_path()
            processor = TrackProcessor()
            
            # Map choice 2 to Audio ('a') and choice 3 to Subtitles ('s')
            stream_type = 'a' if choice == "2" else 's'
            
            # Smart logic to grab a sample file for track identification
            sample_file = target_path
            if os.path.isdir(target_path):
                videos = scan_folder(target_path, ['.mkv', '.mp4', '.avi'])
                sample_file = videos[0] if videos else None
            
            if sample_file and os.path.exists(sample_file):
                # Fetch metadata using ffprobe via the imported TrackProcessor
                tracks = processor.get_track_info(sample_file, stream_type)
                if tracks:
                    print(f"\nAvailable Tracks (Based on {os.path.basename(sample_file)}):")
                    for i, t in enumerate(tracks):
                        print(f"[{i}] {t.get('tags', {}).get('language', 'unknown')} - {t.get('tags', {}).get('title', '')}")
                    
                    # Capture user's desired track IDs and convert to integer list
                    user_input = input("Enter ID(s) to KEEP (e.g., 0,2): ")
                    indices = [int(x.strip()) for x in user_input.split(',') if x.strip().isdigit()]
                    
                    if processor.process_batch(target_path, indices, stream_type):
                        success = True
                else:
                    print("❌ No tracks found.")

        # ---------------------------------------------------------
        # 4 & 5. STREAM MERGER (BATCH AUTOMATION)
        # ---------------------------------------------------------
        # Scans a folder to automatically pair and mux Audio or Subtitle files 
        # into Video containers losslessly (no re-encoding).
        elif choice in ["4", "5"]:
            merger = StreamMerger()
            
            # Option 4: Batch Audio Merging
            if choice == "4":
                print("\n--- BATCH AUDIO MERGER ---")
                print("Name your video and audio files exactly the same (e.g., Ep1.mkv and Ep1.mka)")
                target_folder = get_path("Enter folder path: ")
                if merger.batch_process_folder(target_folder, mode='audio'): 
                    success = True
            
            # Option 5: Batch Subtitle Embedding
            else:
                print("\n--- BATCH SUBTITLE EMBEDDER ---")
                print("Name your video and subtitle files exactly the same (e.g., Movie.mp4 and Movie.srt)")
                target_folder = get_path("Enter folder path: ")
                if merger.batch_process_folder(target_folder, mode='subtitle'): 
                    success = True

        # ---------------------------------------------------------
        # 6. VIDEO STITCHER
        # ---------------------------------------------------------
        # Uses the 'concat demuxer' to join First_Half.mp4 and Second_Half.mp4.
        elif choice == "6":
            folder = get_path("Enter folder containing parts: ")
            ext = input("Extension of parts (e.g., .mp4): ")
            
            # Gathers all parts in alphabetical order
            files = sorted(glob.glob(os.path.join(folder, f"*{ext}")))
            if files:
                out_name = input("Output filename (e.g., FullMovie.mp4): ")
                stitcher = VideoStitcher()
                if stitcher.concat_videos(files, os.path.join(folder, out_name)): success = True

        # ---------------------------------------------------------
        # 7 & 8 & 9. DIVIDER & EDITOR SPLITTING
        # ---------------------------------------------------------
        # Handles all operations related to cutting a video.
        elif choice in ["7", "8", "9"]:
            target_path = get_path()
            
            # Option 7: Intermission (Cut exactly at a specified timestamp)
            if choice == "7":
                split_time = input("Enter intermission time (HH:MM:SS or seconds): ")
                divider = VideoDivider()
                s, p1, p2 = divider.split_at_intermission(target_path, split_time)
                if s: success = True
                
            # Option 8: Chunking (Cut entire video into repeating segments like 30s)
            elif choice == "8":
                sec = input("Enter seconds per chunk (e.g., 30): ")
                divider = VideoDivider()
                if divider.split_by_chunks(target_path, sec): success = True
                
            # Option 9: Extraction (Pull one specific timeframe out of the movie)
            elif choice == "9":
                sec = int(input("Enter duration per segment (seconds): "))
                editor = VideoEditor()
                if editor.split_by_time(target_path, sec): success = True

        # ---------------------------------------------------------
        # 10. EDITOR: SHORTS
        # ---------------------------------------------------------
        # Converts standard 16:9 widescreen video into 9:16 vertical video.
        # Applies a professional gaussian blur to the background automatically.
        elif choice == "10":
            target_path = get_path()
            editor = VideoEditor()
            out = os.path.splitext(target_path)[0] + "_shorts.mp4"
            if editor.convert_to_shorts_style(target_path, out): success = True

        # ---------------------------------------------------------
        # 11. WATERMARK (SMART SINGLE/BATCH)
        # ---------------------------------------------------------
        # Overlays a PNG logo onto the video frames (requires re-encoding).
        # We upgraded this with Smart Folder Detection to brand massive batches.
        elif choice == "11":
            target_path = get_path("Enter Video OR Folder path: ")
            img = get_path("Enter Logo path (.png): ")
            pos = input("Position (br, bl, tr, tl, center) [Default: br]: ") or "br"
            wm = Watermarker()
            
            if os.path.isdir(target_path):
                # Loop through every video in the folder and brand it
                vids = scan_folder(target_path, ['.mp4', '.mkv'])
                for v in vids:
                    out = os.path.splitext(v)[0] + "_branded.mp4"
                    wm.add_image_watermark(v, img, out, pos)
                success = True
            elif os.path.isfile(target_path):
                # Brand a single file
                out = os.path.splitext(target_path)[0] + "_branded.mp4"
                if wm.add_image_watermark(target_path, img, out, pos): success = True

        # ---------------------------------------------------------
        # 12. GIF MAKER
        # ---------------------------------------------------------
        # Generates loopable animations using a two-pass palette algorithm.
        # Presets allow the user to balance generation speed vs visual quality.
        elif choice == "12":
            target_path = get_path()
            start = input("Start time (e.g., 00:00:10): ")
            dur = input("Duration in sec: ")
            preset = input("Preset (ultrafast, fast, medium) [Default: fast]: ") or "fast"
            maker = GifMaker()
            out = os.path.splitext(target_path)[0] + ".gif"
            if maker.create_gif(target_path, out, start, dur, preset=preset): success = True

        # ---------------------------------------------------------
        # 13. COMPRESSOR
        # ---------------------------------------------------------
        # Intelligently scans a directory for massive files (default > 1.5GB) 
        # and recompresses their audio tracks to save space without ruining video quality.
        elif choice == "13":
            folder = get_path("Enter folder path to scan for compression: ")
            compressor = VideoCompressor()
            videos = scan_folder(folder, ['.mkv', '.mp4', '.mov'])
            threshold = float(input("Compress files larger than (GB) [Default: 1.5]: ") or 1.5)
            
            count = 0
            for vid in videos:
                if compressor.get_file_size_gb(vid) > threshold:
                    out = os.path.splitext(vid)[0] + "_compressed.mkv"
                    if compressor.compress_audio_maintain_video(vid, out): count += 1
            if count > 0: success = True

        # ---------------------------------------------------------
        # 14, 15, 16. AUDIO EXTRACTOR
        # ---------------------------------------------------------
        # Rips audio from video files. Uses `-vn` flag to drop video packets.
        elif choice in ["14", "15", "16"]:
            extractor = AudioExtractor()
            fmt = input("Output format (mp3/wav/original): ").lower()
            
            # Option 14: Standard extraction from a single file
            if choice == "14":
                target_path = get_path("Enter Video File path: ")
                s, o = extractor.extract_audio(target_path, fmt)
                if s: success = True
                
            # Option 15: Mass Harvester. Scans a folder recursively for all videos.
            elif choice == "15":
                target_path = get_path("Enter Folder path (Mass Harvest): ")
                if extractor.extract_folder(target_path, fmt): success = True
                
            # Option 16: Targeted. Pulls alternative tracks (like Track 2 / Dubs).
            elif choice == "16":
                target_path = get_path("Enter Video File path: ")
                tid = int(input("Enter Track ID to extract (e.g., 1 for second track): "))
                s, o = extractor.extract_audio(target_path, fmt, track_id=tid)
                if s: success = True

        # ---------------------------------------------------------
        # 17 & 18. AI REMASTER
        # ---------------------------------------------------------
        # Enhances legacy/vintage video using advanced filtering and scaling.
        elif choice == "17":
            # Option 17: Standard Enhancement (Denoiser/Upscaler)
            target_path = get_path("Old video path: ")
            remaster = VideoRemaster()
            out = os.path.splitext(target_path)[0] + "_remastered.mp4"
            if remaster.enhance_old_footage(target_path, out): success = True
            
        elif choice == "18":
            # Option 18: GPU-Heavy AI Restoration (Requires Nvidia RTX hardware)
            movie_path = get_path("Enter path to old movie (1980s-2005): ")
            if os.path.exists(movie_path):
                engine = RemasterService()
                try:
                    print("\n[*] Creating a 2-minute theatrical sample...")
                    sample = engine.generate_sample(movie_path)
                    print(f"[DONE] Check sample at: {sample}")
                    if input("\nStart full 12-18 hour remaster? (y/n): ").lower() == 'y':
                        if engine.start_full_remaster(movie_path): success = True
                except Exception as e:
                    print(f"\n[CRITICAL ERROR] Failed: {e}")
        # ---------------------------------------------------------
        # 20. ARCHIVER
        # ---------------------------------------------------------
        elif choice == "20":
            target_folder = get_path("Enter parent directory to archive: ")
            
            if os.path.exists(target_folder):
                print("\n--- Archive Mode ---")
                print(" [1] Package Only (Lightning Fast - Best for Videos/Media)")
                print(" [2] Compress & Package (Slower - Best for Docs/Code)")
                mode_choice = input("Select mode (1/2) [Default: 1]: ").strip()
                
                # If they select 2, we turn compression ON. Otherwise, it stays OFF.
                do_compress = True if mode_choice == "2" else False
                
                archiver = FolderArchiver()
                if archiver.batch_zip_folders(target_folder, compress=do_compress): 
                    success = True
            else:
                print(f"❌ Path not found: {target_folder}")
        # ---------------------------------------------------------
        # 21. UN-ARCHIVER (7-ZIP ENGINE)
        # ---------------------------------------------------------
        elif choice == "21":
            target_zip = get_path("Enter the path to the .zip file: ")
            
            unarchiver = EnterpriseUnarchiver()
            if unarchiver.extract_archive(target_zip):
                success = True
        # Inside your Menu UI / Terminal Interface:
        elif choice == "22":
            print("\n" + "="*50)
            print("      INITIATING FEATURE 22: SEAMLESS SUTURE")
            print("="*50)
            print("This tool will automatically find the exact visual overlap")
            print("between split movie parts and merge them natively with zero")
            print("quality loss or timeline freezing.")
            print("-" * 50)
    
            # 1. Gather the target directory from the user
            target_folder = input("Enter the Folder Path containing the split parts:\n> ").strip().replace('"', '')
    
            # 2. Execute the independent module
            # We wrap it in a basic try/except just in case the user provides a completely broken path
            try:
                print("\nHanding over to Seamless Suture Engine...")
                seamless_suture.run_suture_workflow(target_folder)
            except Exception as e:
                print(f"\n[CRITICAL ERROR] The Seamless Suture module failed: {e}")
        
            print("\nReturning to VidFlow Main Menu...")

# ... (the rest of your loop) ...
        else:
            print("❌ Invalid option.")
        

        # --- END OF LOOP CHECK ---
        # Instead of risking an UnboundLocalError inside the massive if/elif chain,
        # we check the global success state here and report it back to the user.
        if success:
            print("\n✨ Operation Completed Successfully")
        else:
            print("\n⚠️ Operation Finished/Failed (Check logs)")
        
        input("\nPress Enter to return to menu...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Failsafe: Handles Ctrl+C cleanly without throwing ugly Python tracebacks
        print("\n\nForce quitting VidFlow... Goodbye!")
        sys.exit(0)

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