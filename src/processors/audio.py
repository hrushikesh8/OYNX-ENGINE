# --- 2/3. CLEAN TRACKS (Batch or Single) ---
    elif choice in ["2", "3"]:
        path = input("Enter video path OR folder path: ").strip('"')
        processor = TrackProcessor() # Uses our crash-proof processor!
        stream_type = 'a' if choice == "2" else 's'
        label = "Audio" if choice == "2" else "Subtitle"

        # 1. Detect if it's a single file or a folder
        tasks = []
        if os.path.isdir(path):
            videos = scan_folder(path, ['.mkv', '.mp4', '.avi'])
            tasks.extend(videos)
            print(f"📂 Detected folder. Found {len(tasks)} videos.")
        elif os.path.isfile(path):
            tasks.append(path)
        else:
            print("❌ Invalid path.")
            continue # Skip to end of loop

        if not tasks:
            print("❌ No videos found to process.")
            continue

        # 2. Use the FIRST file to map out the tracks
        sample_file = tasks[0]
        tracks = processor.get_track_info(sample_file, stream_type)
        
        if not tracks:
            print(f"❌ No {label} tracks found in {os.path.basename(sample_file)}.")
        else:
            print(f"\nAvailable {label} Tracks (Based on {os.path.basename(sample_file)}):")
            for i, t in enumerate(tracks):
                lang = t.get('tags', {}).get('language', 'unknown')
                title = t.get('tags', {}).get('title', '')
                print(f"[{i}] {lang} {title}")

            # 3. Get user selection
            user_input = input(f"Enter ID(s) to KEEP (comma separated, e.g., 0,2): ")
            try:
                indices = [int(x.strip()) for x in user_input.split(',')]
                
                print(f"🚀 Processing {len(tasks)} files...")
                print("-" * 40)
                
                success_count = 0
                
                # 4. Loop through all tasks and apply the cleanup
                for vid in tasks:
                    print(f"   ⏳ Cleaning: {os.path.basename(vid)}...")
                    out_path = os.path.splitext(vid)[0] + f"_clean_{label.lower()}.mkv"
                    
                    if processor.keep_multiple_tracks(vid, out_path, indices, stream_type):
                        print(f"   ✅ Saved: {os.path.basename(out_path)}")
                        success_count += 1
                        success = True
                    else:
                        print(f"   ❌ Failed: {os.path.basename(vid)}")
                        
                print("-" * 40)
                print(f"🎉 Batch Complete. Successfully processed {success_count}/{len(tasks)} files.")

            except ValueError:
                print("❌ Invalid input. Please enter numbers separated by commas.")