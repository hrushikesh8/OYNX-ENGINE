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

    choice = input("\nSelect an option (1-13): ")
    
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

    # --- 2/3. CLEAN TRACKS ---
    elif choice in ["2", "3"]:
        path = input("Enter video path: ").strip('"')
        processor = TrackProcessor()
        stream_type = 'a' if choice == "2" else 's'
        label = "Audio" if choice == "2" else "Subtitle"

        tracks = processor.get_track_info(path, stream_type)
        if not tracks:
            print(f"❌ No {label} tracks found.")
        else:
            print(f"\nAvailable {label} Tracks:")
            for i, t in enumerate(tracks):
                lang = t.get('tags', {}).get('language', 'unknown')
                title = t.get('tags', {}).get('title', '')
                print(f"[{i}] {lang} {title}")

            user_input = input(f"Enter ID(s) to KEEP (comma separated, e.g., 0,2): ")
            try:
                indices = [int(x.strip()) for x in user_input.split(',')]
                out_path = os.path.splitext(path)[0] + f"_clean_{label.lower()}.mkv"
                print("Processing...")
                if processor.keep_multiple_tracks(path, out_path, indices, stream_type):
                    print(f"✅ Saved to: {out_path}")
                    success = True
            except ValueError:
                print("Invalid input.")

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
        success, out = extractor.extract_audio(path, fmt)
        
        if success:
            print(f"✅ Audio saved to: {out}")
        else:
            print("❌ Extraction failed.")

    # ✅ FIX 2: Check success safely (it will always exist now)
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

1.  **Architecture (Modular Design)**:
    -   This `main.py` acts as the **Orchestrator**. It does not contain the 
        heavy video processing logic itself. 
    -   Instead, it imports specialized classes (e.g., `VideoEditor`, `TrackProcessor`) 
        from the `src.processors` package. This adheres to the "Separation of Concerns" 
        principle, making the project easy to maintain and expand.

2.  **Dependency Check (`SystemUtils`)**:
    -   Before showing the menu, the script runs `check_ffmpeg_availability()`.
    -   This ensures the core engine (FFmpeg) is installed on the host machine, 
        preventing crashes later in the execution.

3.  **The `scan_folder` Utility**:
    -   A helper function used for batch operations (like Options 4 & 5).
    -   It uses `glob` to recursively find all video files in a directory, 
        allowing the user to process entire seasons of shows or playlists at once.

4.  **Input Handling & Dispatch**:
    -   The script uses a simple CLI (Command Line Interface) menu.
    -   It captures user input (`choice`) and uses an `if-elif` structure to 
        route the request to the correct processor.
    -   Example: If user selects '7', the `VideoEditor` class is instantiated 
        to handle the splitting logic.

5.  **Error Handling**:
    -   `try-except` blocks are placed around numerical inputs (like timestamps 
        or track IDs) to prevent the program from crashing if a user types 
        invalid text.

        and to ensure that the `success` variable is always defined, 
        it is initialized at the start of the `main()` function. This prevents any `UnboundLocalError` when
        checking the success status at the end of the function.

        there are 12 different functions that can be called from the main function,
          each of them has its own error handling and success variable, 
          but to prevent any unbound local error, the success variable is initialized 
          at the start of the main function, and then updated based on the success of each operation.

-----------------------------------------------------------------------
"""