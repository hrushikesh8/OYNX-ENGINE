import os
import re
import shutil
import csv
from datetime import datetime

from src.processors.chronicle.tmdb_api import get_episode_names, get_all_episodes_data, get_show_id
from src.processors.time_machine import TimeMachine

def organize_and_rename(master_folder, show_name, api_key, show_id, dry_run=True, run_id=None):
    # Fetch show_id if not provided
    if show_id is None:
        fetched_id, _ = get_show_id(api_key, show_name)
        if fetched_id:
            show_id = fetched_id
            print(f"📡 Found TVMaze ID for '{show_name}': {show_id}")
        else:
            print(f"⚠️ TVMaze could not find '{show_name}'. Falling back to Offline Mode (No Official Titles).")

    # ---> ADD THIS LINE TO FIX THE BUG <---
    show_name = "".join(c for c in show_name if c not in r'\/:*?"<>|')

    # The upgraded Regex: Catches 'S01E01', 's1 e1', '1x01', and ignores '1920x1080'
    pattern = r'(?<!\d)[Ss]?(\d{1,3})[\s\.\-]*[EeXx](\d{1,4})(?!\d)' 
    
    # What kind of files do we actually care about?
    video_exts = ('.mkv', '.mp4', '.avi', '.m4v')
    sub_exts = ('.srt', '.ass', '.vtt')
    junk_exts = ('.txt', '.nfo', '.url', '.ini', '.jpg', '.png')
    
    # Grab every file in the messy folder and force them into alphabetical order
    # This prevents 'Season 07' from being created before 'Season 01'
    all_files = [f for f in os.listdir(master_folder) if os.path.isfile(os.path.join(master_folder, f))]
    all_files.sort() 
    
    # Separate the media from the subtitles
    video_files = [f for f in all_files if f.lower().endswith(video_exts)]
    sub_files = [f for f in all_files if f.lower().endswith(sub_exts)]
    
    # ---> ADD THESE TWO DIAGNOSTIC LINES RIGHT HERE <---
    print(f"DIAGNOSTIC: Found {len(all_files)} total files.")
    print(f"DIAGNOSTIC: Found {len(video_files)} valid video files.")
    
    # A temporary dictionary to hold Season data so we don't spam the API asking for the same season twice
    season_data_cache = {} 
    
    if not video_files:
        print(f"⚠️ No video files found in {master_folder}")
        return

    print(f"\n🎬 Processing '{show_name}' in '{master_folder}'")
    print("-" * 50)

    # Start the history log session if this is a real run (not a simulation)
    if not dry_run:
        os.makedirs("logs", exist_ok=True)

    # --- MAIN LOOP: Process every video file one by one ---
    for filename in video_files:
        match = re.search(pattern, filename)
        if not match: continue # If it doesn't have an episode number, skip it.
            
        season_num = int(match.group(1))
        episode_num = int(match.group(2))
        
        # If we haven't downloaded this season's titles yet, fetch them now
        if season_num not in season_data_cache:
            if show_id:
                season_data_cache[season_num] = get_episode_names(api_key, show_id, season_num)
            else:
                season_data_cache[season_num] = [] # Offline mode fallback
            
        episodes_list = season_data_cache[season_num]
        
        # Fallback to a generic title if the episode exceeds the fetched list or if we're offline
        if not episodes_list or episode_num > len(episodes_list):
            official_title = f"Episode {episode_num:02d}"
        else:
            official_title = episodes_list[episode_num - 1]
            
        # Get the official title and scrub out characters that Windows hates in folder names
        clean_title = "".join(c for c in official_title if c not in r'\/:*?"<>|')
        
        # Scrape the file name for quality tags (1080p) and multi-part tags (pt1)
        quality_match = re.search(r'(1080p|720p|2160p|4k|480p)', filename, re.IGNORECASE)
        quality_tag = f" [{quality_match.group(1).lower()}]" if quality_match else ""

        part_match = re.search(r'(?i)(?:pt|part|cd|disc)[\s\.\-\_]*(\d+[a-c]?)', filename)
        part_tag = f" - Part {part_match.group(1)}" if part_match else ""
        
        # Assemble the perfect final file name
        base_new_name = f"{show_name} S{season_num:02d}E{episode_num:02d} - {clean_title}{part_tag}{quality_tag}"
        video_ext = os.path.splitext(filename)[1]
        
        season_folder_path = os.path.join(master_folder, f"{show_name} Season {season_num:02d}")
        old_video_path = os.path.join(master_folder, filename)
        new_video_path = os.path.join(season_folder_path, base_new_name + video_ext)
        
        # --- EXECUTION BLOCK ---
        if not dry_run:
            os.makedirs(season_folder_path, exist_ok=True) # Create Season folder if it doesn't exist
            
            # Conflict Resolution: If a file already exists here with this name, append '_v2'
            if os.path.exists(new_video_path) and old_video_path != new_video_path:
                new_video_path = os.path.join(season_folder_path, base_new_name + f"_v2{video_ext}")
                print(f"⚠️ Collision Avoided: Appended _v2")
                
            shutil.move(old_video_path, new_video_path) # Actually move the file
            print(f"[MOVED] 🎞️ -> {f'{show_name} Season {season_num:02d}'}\\{os.path.basename(new_video_path)}")
            
            # ---> NEW TIME MACHINE LOGGING FOR VIDEO <---
            if run_id:
                TimeMachine.log_action("Chronicle", run_id, "ORGANIZE_VIDEO", old_video_path, new_video_path, op_type="RENAME")
                
        else:
            print(f"[DRY RUN] 🎞️ '{filename}' -> '{os.path.basename(new_video_path)}'")

        # --- SUBTITLE SYNC BLOCK ---
        # Hunt through the subtitle files to find a perfect match for the video we just moved
        for sub in sub_files:
            sub_match = re.search(pattern, sub)
            if sub_match and int(sub_match.group(1)) == season_num and int(sub_match.group(2)) == episode_num:
                
                # Ensure we don't accidentally sync Part 2's subtitles to Part 1's video
                sub_part_match = re.search(r'(?i)(?:pt|part|cd|disc)[\s\.\-\_]*(\d+[a-c]?)', sub)
                if part_match and sub_part_match and part_match.group(1) != sub_part_match.group(1):
                    continue 
                    
                sub_ext = os.path.splitext(sub)[1]
                old_sub_path = os.path.join(master_folder, sub)
                new_sub_path = os.path.join(season_folder_path, base_new_name + sub_ext) # Clones the video name perfectly
                
                if not dry_run:
                    if os.path.exists(new_sub_path) and old_sub_path != new_sub_path:
                        new_sub_path = os.path.join(season_folder_path, base_new_name + f"_v2{sub_ext}")
                    
                    shutil.move(old_sub_path, new_sub_path)
                    print(f"          📝 -> {f'{show_name} Season {season_num:02d}'}\\{os.path.basename(new_sub_path)}")
                    
                    # ---> NEW TIME MACHINE LOGGING FOR SUBTITLES <---
                    if run_id:
                        TimeMachine.log_action("Chronicle", run_id, "SYNC_SUBTITLE", old_sub_path, new_sub_path, op_type="RENAME")
                        
                else:
                    print(f"          📝 '{sub}' -> '{os.path.basename(new_sub_path)}'")
        if dry_run: print("") 

    # --- JUNK SWEEPER ---
    # Delete leftover .txt or .nfo files and scrap empty folders left behind
    if not dry_run:
        print("\n🧹 Sweeping up junk files...")
        for root, dirs, files in os.walk(master_folder, topdown=False):
            for f in files:
                if f.lower().endswith(junk_exts):
                    os.remove(os.path.join(root, f))
            if not os.listdir(root):
                try: os.rmdir(root)
                except OSError: pass

    print("-" * 50)
    if not dry_run: print("✅ BingePrep Complete! Files are sorted and folders are sanitized.")

def audit_missing_episodes(master_folder, show_name, api_key, show_id):
    # Reads your local drive and compares it to TVMaze to find missing files
    pattern = r'[Ss](\d+)[\s\.\-]*[EeXx](\d+)' 
    valid_ext = ('.mkv', '.mp4', '.avi', '.m4v')
    local_episodes = set()
    
    # 1. Scan your hard drive
    for root, dirs, files in os.walk(master_folder):
        for filename in files:
            if filename.lower().endswith(valid_ext):
                match = re.search(pattern, filename)
                if match: local_episodes.add((int(match.group(1)), int(match.group(2))))
                    
    # 2. Ask the Brain for the official TVMaze list
    official_data = get_all_episodes_data(api_key, show_id)
    if not official_data: return
        
    print(f"\n🕵️ Auditing '{show_name}' Library...")
    print("=" * 50)
    
    missing_count = 0
    current_season = -1
    
    # 3. Compare the two lists and print what's missing
    for ep in official_data:
        s_num, e_num, title = ep.get('season'), ep.get('number'), ep.get('name')
        if s_num is None or e_num is None or s_num == 0: continue
            
        if (s_num, e_num) not in local_episodes:
            if s_num != current_season:
                print(f"\n📁 Season {s_num:02d}:")
                current_season = s_num
            print(f"  ❌ Missing: E{e_num:02d} - {title}")
            missing_count += 1
            
    print("\n" + "=" * 50)
    if missing_count == 0: print("🎉 Your library is 100% complete!")
    else: print(f"⚠️ Total missing episodes: {missing_count}")




# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.file_manager import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (file_manager.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'file_manager.py', is a core component of the Onyx Engine. It is
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
