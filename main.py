import os
import glob
import sys
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
from src.processors.remaster_service import RemasterService

def scan_folder(folder_path, extensions):
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(glob.escape(folder_path), '**', f'*{ext}'), recursive=True))
    return files

def main():
    if not SystemUtils.check_ffmpeg_availability():
        print("❌ CRITICAL: FFmpeg not found. Please install it and add to PATH.")
        return

    print("\n=== 🎬 VidFlow Engine v1.5 (Enterprise) ===")
    print("1.  Convert Video Format")
    print("2.  Clean Audio Tracks (Multi-Select)")
    print("3.  Clean Subtitle Tracks (Multi-Select)")
    print("4.  Batch Merge Subtitles (Auto-Match)")
    print("5.  Smart Compressor (Reduce Audio Size)")
    print("6.  Auto-Create Shorts (9:16 Layout)")
    print("7.  Split Video for Social Media")
    print("8.  Stitch/Join Multiple Videos")
    print("9.  Add Watermark/Logo")
    print("10. Create High-Quality GIF")
    print("11. Remaster Old Footage (Denoise + Upscale)")
    print("12. Division (Split into 2 Parts)")
    print("13. Extract Audio (MP3/WAV)")
    print("14. Theatrical Remaster (AI Restoration) [Hidden Test Option]")

    choice = input("\nSelect an option (1-14): ")
    
    # ✅ FIX 1: Initialize success variable globally here
    success = False

    # --- 1. CONVERT ---
    # --- 1. CONVERT (Hybrid Mode) ---
    if choice == "1":
        print("\n--- Conversion Mode ---")
        print("1. Batch Convert (Entire Folder)")
        print("2. Single Convert (One File)")
        sub_choice = input("Select mode (1/2): ")
        
        processor = FormatMapper()
        
        # Common inputs
        fmt = input("Target format (mp4/mkv/avi): ").lower()
        
        # MODE 1: BATCH
        if sub_choice == "1":
            folder_path = input("Enter Source Folder: ").strip('"')
            if os.path.exists(folder_path):
                # Create a "converted" folder inside the source
                output_dir = os.path.join(folder_path, "converted")
                processor.process_input(folder_path, output_dir, fmt)
                success = True
            else:
                print("❌ Folder not found.")

        # MODE 2: SINGLE
        elif sub_choice == "2":
            file_path = input("Enter File Path: ").strip('"')
            if os.path.exists(file_path):
                # Create a "converted" folder in the same directory as the file
                output_dir = os.path.join(os.path.dirname(file_path), "converted")
                processor.process_input(file_path, output_dir, fmt)
                success = True
            else:
                print("❌ File not found.")
        
        else:
            print("Invalid selection.")

    # --- 2 & 3. CLEAN TRACKS (Audio or Subtitles - Batch/Single) ---
    elif choice in ["2", "3"]:
        path = input("Enter video OR folder path: ").strip('"')
        processor = TrackProcessor()
        
        # Smart toggle: If choice 2, do Audio ('a'). If choice 3, do Subtitles ('s').
        stream_type = 'a' if choice == "2" else 's'
        label = "Audio" if choice == "2" else "Subtitle"

        # 1. Find a sample file to read the tracks from
        sample_file = path
        if os.path.isdir(path):
            videos = scan_folder(path, ['.mkv', '.mp4', '.avi'])
            if not videos:
                print("❌ No videos found in this folder.")
                success = False
            else:
                sample_file = videos[0]
        
        if sample_file and os.path.exists(sample_file):
            # 2. Get tracks from the sample file
            tracks = processor.get_track_info(sample_file, stream_type)
            
            if not tracks:
                print(f"❌ No {label} tracks found in {os.path.basename(sample_file)}.")
            else:
                print(f"\nAvailable {label} Tracks (Based on {os.path.basename(sample_file)}):")
                for i, t in enumerate(tracks):
                    lang = t.get('tags', {}).get('language', 'unknown')
                    title = t.get('tags', {}).get('title', '')
                    print(f"[{i}] {lang} {title}")

                # 3. Get user selection and run the batch processor
                user_input = input("Enter ID(s) to KEEP (comma separated, e.g., 0,2): ")
                try:
                    indices = [int(x.strip()) for x in user_input.split(',')]
                    
                    # Run the batch processor!
                    if processor.process_batch(path, indices, stream_type):
                        success = True
                except ValueError:
                    print("❌ Invalid input. Please enter numbers separated by commas.")

    # --- 4. SMART MERGE (Batch or Single) ---
    elif choice == "4":
        print("\n--- Merge Mode ---")
        print("1. Batch Merge (Folder - Auto Match by Name)")
        print("2. Single Merge (Manually Select Files)")
        sub_choice = input("Select mode (1/2): ")

        merger = StreamMerger()

        # MODE 1: BATCH (Folder)
        if sub_choice == "1":
            folder = input("Enter folder path: ").strip('"')
            merge_type = input("Merge Subtitles (s) or Audio (a)? ").lower()
            
            videos = scan_folder(folder, ['.mkv', '.mp4', '.avi'])
            print(f"📂 Found {len(videos)} videos. Scanning for matches...")
            
            count = 0
            for vid_path in videos:
                base = os.path.splitext(vid_path)[0]
                found_match = None
                
                # Logic for Subtitles
                if merge_type == 's':
                    for ext in ['.srt', '.ass']:
                        if os.path.exists(base + ext):
                            found_match = base + ext
                            break
                    if found_match:
                        out = base + "_subbed.mkv"
                        if merger.mux_subtitles(vid_path, found_match, out): count += 1

                # Logic for Audio
                elif merge_type == 'a':
                    for ext in ['.mp3', '.m4a', '.ac3', '.wav']:
                        if os.path.exists(base + ext):
                            found_match = base + ext
                            break
                    if found_match:
                        out = base + "_merged.mkv"
                        if merger.merge_video_audio(vid_path, found_match, out): count += 1

            if count > 0:
                success = True
                print(f"\n🎉 Batch processing complete. Merged {count} files.")
            else:
                print("⚠️ No matching subtitle/audio files found in this folder.")

        # MODE 2: SINGLE (Manual)
        elif sub_choice == "2":
            vid_path = input("Enter Video Path: ").strip('"')
            type_choice = input("Merge Subtitle (s) or Audio (a)? ").lower()
            
            if not os.path.exists(vid_path):
                print("❌ Video file not found.")
            else:
                if type_choice == 's':
                    sub_path = input("Enter Subtitle Path (.srt/.ass): ").strip('"')
                    if os.path.exists(sub_path):
                        out = os.path.splitext(vid_path)[0] + "_subbed.mkv"
                        if merger.mux_subtitles(vid_path, sub_path, out): success = True
                    else:
                        print("❌ Subtitle file not found.")

                elif type_choice == 'a':
                    aud_path = input("Enter Audio Path: ").strip('"')
                    if os.path.exists(aud_path):
                        out = os.path.splitext(vid_path)[0] + "_merged.mkv"
                        if merger.merge_video_audio(vid_path, aud_path, out): success = True
                    else:
                        print("❌ Audio file not found.")

    # --- 5. COMPRESS ---
    elif choice == "5":
        folder = input("Enter folder path: ").strip('"')
        compressor = VideoCompressor()
        videos = scan_folder(folder, ['.mkv', '.mp4', '.mov'])
        threshold = 1.5 
        
        count = 0
        for vid in videos:
            if compressor.get_file_size_gb(vid) > threshold:
                print(f"📉 Compressing: {os.path.basename(vid)}")
                out = os.path.splitext(vid)[0] + "_compressed.mkv"
                compressor.compress_audio_maintain_video(vid, out)
                count += 1
        success = True

    # --- 6. SHORTS ---
    elif choice == "6":
        path = input("Enter video path: ").strip('"')
        editor = VideoEditor()
        out = os.path.splitext(path)[0] + "_shorts.mp4"
        if editor.convert_to_shorts_style(path, out):
            print(f"✅ Created: {out}")
            success = True

    # --- 7. SPLIT ---
    elif choice == "7":
        path = input("Enter video path: ").strip('"')
        sec = int(input("Enter duration per part (seconds): "))
        editor = VideoEditor()
        editor.split_by_time(path, sec)
        success = True

    # --- 8. STITCH ---
    elif choice == "8":
        folder = input("Enter folder with videos: ").strip('"')
        ext = input("Extension (e.g., .mp4): ")
        files = sorted(glob.glob(os.path.join(folder, f"*{ext}")))
        if files:
            out_name = input("Output filename: ")
            stitcher = VideoStitcher()
            stitcher.concat_videos(files, os.path.join(folder, out_name))
            success = True

    # --- 9. WATERMARK ---
    elif choice == "9":
        vid = input("Video path: ").strip('"')
        img = input("Logo path: ").strip('"')
        pos = input("Position (br, bl, tr, tl, center): ")
        wm = Watermarker()
        out = os.path.splitext(vid)[0] + "_branded.mp4"
        if wm.add_image_watermark(vid, img, out, pos):
            success = True

    # --- 10. GIF ---
    elif choice == "10":
        path = input("Video path: ").strip('"')
        start = int(input("Start (sec): "))
        dur = int(input("Duration (sec): "))
        maker = GifMaker()
        out = os.path.splitext(path)[0] + ".gif"
        maker.create_high_quality_gif(path, out, start, dur)
        success = True

    # --- 11. REMASTER ---
    elif choice == "11":
        path = input("Old video path: ").strip('"')
        remaster = VideoRemaster()
        out = os.path.splitext(path)[0] + "_remastered.mp4"
        remaster.enhance_old_footage(path, out)
        success = True
    
# --- 12: DIVIDER ---
    elif choice == "12":
        path = input("Enter video path: ").strip('"')
        
        # We removed the 'float()' wrapper so it accepts colons perfectly
        print("Tip: You can use seconds (3600) OR format like HH:MM:SS (01:00:00)")
        split_time = input("Enter split time: ").strip()
        
        divider = VideoDivider()
        s, p1, p2 = divider.split_at_intermission(path, split_time)
        
        if s:
            print(f"✅ Division Successful!")
            print(f"   Part 1: {os.path.basename(p1)}")
            print(f"   Part 2: {os.path.basename(p2)}")
            success = True
        else:
            print("❌ Division failed.")

    # --- 13: EXTRACT AUDIO ---
    elif choice == "13":
        path = input("Enter video path: ").strip('"')
        fmt = input("Output format (mp3/wav/original): ").lower()

        extractor = AudioExtractor()
        # Captures success status from the extractor
        success_status, out = extractor.extract_audio(path, fmt)
        
        if success_status:
            print(f"✅ Audio saved to: {out}")
            success = True
        else:
            print("❌ Extraction failed.")

    # --- 14: THEATRICAL REMASTER (AI Restoration) ---
    elif choice == "14":
        print("\n" + "="*50)
        print("      VIDFLOW FEATURE #14: THEATRICAL REMASTER      ")
        print("="*50)
        
        # Prompt for input and clean the path
        movie_path = input("Enter path to the movie file (1980s-2005): ").strip('"').strip("'")
        
        if not os.path.exists(movie_path):
            print(f"[!] Error: File '{movie_path}' not found. Please check the path.")
        else:
            # Initialize the engine from our new service file
            engine = RemasterService()

            try:
                # Phase 1: The Sample (The 'Extractor' logic)
                print("\n[*] Initializing Engine and RTX GPU...")
                print("[*] Creating a 2-minute theatrical sample for review...")
                sample_file = engine.generate_sample(movie_path)
                
                print(f"\n[DONE] Sample generated at: {sample_file}")
                print("[?] ACTION REQUIRED: Open the sample and check for:")
                print("    - Skin textures (no 'plastic' look)")
                print("    - Color vibrancy")
                print("    - Cinematic film grain")

                # Phase 2: User Validation
                sub_choice = input("\nStart full 12-18 hour remaster? (y/n): ").lower()

                if sub_choice == 'y':
                    print("\n" + "!"*50)
                    print("FULL REMASTER IN PROGRESS")
                    print("The system will handle all steps automatically.")
                    print("Please ensure your RTX GPU is well-ventilated.")
                    print("!"*50 + "\n")
                    
                    final_video = engine.start_full_remaster(movie_path)
                    print(f"\n[SUCCESS] Restoration Complete!")
                    print(f"--> Final File: {final_video}")
                    success = True
                else:
                    print("\n[X] Full process cancelled. Returning to main menu.")

            except Exception as e:
                print(f"\n[CRITICAL ERROR] The remastering process failed: {e}")

    # ✅ FINAL CHECK: This must be at the very end of the main() function
    if success:
        print("\n✨ Operation Completed Successfully")
    else:
        print("\n⚠️ Operation Finished (Check logs for details)")

if __name__ == "__main__":
    main()


"""
-----------------------------------------------------------------------
                           CODE EXPLANATION
-----------------------------------------------------------------------

1.  Architecture (Modular Design):
    -   This `main.py` acts as the Orchestrator. It does not contain the 
        heavy video processing logic itself. 
    -   Instead, it imports specialized classes (e.g., `VideoEditor`, 
        `TrackProcessor`, `RemasterService`) from the `src.processors` package. 
        This adheres to the "Separation of Concerns" principle, making the 
        project highly maintainable, readable, and easy to expand.

2.  Dependency Check (`SystemUtils`):
    -   Before showing the menu, the script runs `check_ffmpeg_availability()`.
    -   This ensures the core engine (FFmpeg) is installed and accessible 
        on the host machine, preventing critical crashes later in the execution.

3.  Hybrid Processing (Batch & Single):
    -   The engine features smart path detection utilizing the `scan_folder` helper.
    -   Many modules (Conversion, Track Cleaning, Merging, Extraction) automatically 
        detect whether the user provided a single file or an entire directory.
    -   If a folder is provided, the script recursively finds all compatible media 
        files and processes entire seasons or playlists simultaneously.

4.  Input Handling & Dispatch (14 Modules):
    -   The script uses a clear CLI (Command Line Interface) menu.
    -   It captures user input (`choice`) and uses an `if-elif` routing structure 
        to direct the request to 1 of 14 distinct specialized processors.
    -   Example: If the user selects '14', the `RemasterService` class is 
        instantiated to handle the AI restoration logic.

5.  State Management & Safety (`success` Flag):
    -   To ensure program stability, a `success` variable is initialized to `False` 
        at the very start of the `main()` function. 
    -   While each of the 14 functions contains its own specific error handling 
        (e.g., catching invalid timestamps, broken codecs, or bad inputs), they all 
        report back to this global flag.
    -   If an operation succeeds, it explicitly updates `success = True`. This 
        guarantees that the final completion check at the end of the script will 
        never throw an `UnboundLocalError`.

-----------------------------------------------------------------------
"""