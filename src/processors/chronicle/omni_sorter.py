import os
import re
import shutil
import requests
from src.processors.chronicle.file_manager import organize_and_rename
from src.processors.time_machine import TimeMachine

def guess_tv_show_info(filename):
    """
    Heuristic Regex Logic: 
    Why was this written? Raw dump folders contain messy file names (e.g. 'the.boys.s01e01.1080p.mkv').
    This function uses a regular expression to find the 'Season/Episode' tag (like S01E01, 1x01, or Season 1).
    Once it finds this boundary, it assumes everything BEFORE it is the show's name.
    """
    # Compile the pattern to match standard episode tags, ignoring case.
    tv_pattern = re.compile(r'(?i)(.+?)[\.\s\-\_]*(?:s\d+e\d+|\d+x\d+|season\s*\d+)')
    match = tv_pattern.search(filename)
    if match:
        # If a match is found, extract the first group (the show name).
        # We replace dots with spaces because many torrent/web rips use '.' instead of spaces.
        raw_name = match.group(1).replace('.', ' ').strip()
        return raw_name
    
    # Return None if no TV tag is found, meaning it's either a movie or an unrecognized format.
    return None

def process_omni_dump(dump_folder, dry_run=True, run_id=None):
    print(f"\n🌪️ Igniting Omni-Sorter for: '{dump_folder}'")
    print("-" * 50)
    
    valid_exts = ('.mkv', '.mp4', '.avi', '.m4v', '.srt', '.ass')
    
    try:
        files = [f for f in os.listdir(dump_folder) if os.path.isfile(os.path.join(dump_folder, f)) and f.lower().endswith(valid_exts)]
    except FileNotFoundError:
        print("❌ Error: Dump folder path does not exist.")
        return

    # 1. Group files by their heuristic guess
    shows_found = {}
    movies_found = []

    for f in files:
        guessed_name = guess_tv_show_info(f)
        if guessed_name:
            if guessed_name not in shows_found:
                shows_found[guessed_name] = []
            shows_found[guessed_name].append(f)
        else:
            # If it lacks a TV tag, it's either a movie or junk
            movies_found.append(f)

    if not shows_found and not movies_found:
        print("⚠️ No valid media files found in the dump.")
        return

    # 2. Process the TV Shows (The Blind Faith Pipeline)
    for raw_name, show_files in shows_found.items():
        print(f"\n🔍 Analyzing heuristic guess: '{raw_name}'...")
        
        url = f"https://api.tvmaze.com/singlesearch/shows?q={raw_name}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                raw_title = data.get('name')
                premiered = data.get('premiered') # Gets format "2019-07-25"
                
                # Chop off the month and day, and format it as "Title (Year)"
                if premiered:
                    year = premiered.split('-')[0]
                    official_name = f"{raw_title} ({year})"
                else:
                    official_name = raw_title
                    
                show_id = data.get('id')
                
                print(f"   ✅ API Match: '{official_name}' (ID: {show_id})")
                
                # Create a staging directory for this specific show
                staging_folder = os.path.join(dump_folder, official_name)
                
                if not dry_run:
                    os.makedirs(staging_folder, exist_ok=True)
                    for file in show_files:
                        old_path = os.path.join(dump_folder, file)
                        new_path = os.path.join(staging_folder, file)
                        shutil.move(old_path, new_path)
                        if run_id:
                            TimeMachine.log_action("Chronicle", run_id, "STAGING_MOVE", old_path, new_path, op_type="RENAME")
                    
                    # 🚀 The Handoff: Trigger the bulletproof engine on the new folder
                    print(f"   🔄 Handing off to BingePrep Engine...")
                    organize_and_rename(staging_folder, official_name, None, show_id, dry_run=False, run_id=run_id)
                else:
                    print(f"   [DRY RUN] Would group {len(show_files)} files and process as '{official_name}'.")

        except Exception as e:
            print(f"   ❌ API Error or Show not found for '{raw_name}': {e}")

    # 3. Warn the user about Movies
    if movies_found:
        print("\n🍿 Movie / Unidentified Pipeline:")
        for m in movies_found:
            print(f"   🎞️ {m}")
        print("   (Chronicle currently only processes TV Shows. These files were left untouched.)")
        
    print("\n" + "-" * 50)
    print("✅ Omni-Dump Processing Complete.")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.chronicle.omni_sorter import process_omni_dump
# 
# # Point it to a messy download directory:
# dump_dir = "C:/Downloads/Messy TV Shows"
# process_omni_dump(dump_dir, dry_run=False)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: THE OMNI-SORTER (omni_sorter.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file acts as the initial "Intake Funnel" for the Chronicle Organizer.
#    When users have a massive folder filled with dozens of different TV shows 
#    all mixed together, this script untangles them. It groups them by name, 
#    pings the TVMaze API to get their official structured titles and release 
#    years, and then moves them into isolated staging folders.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    It iterates over all video files in a target directory. Using heuristic
#    regex matching, it identifies which files belong to the same TV show. 
#    It then hits a REST API to sanitize the show name (e.g., changing 
#    "the boys" to "The Boys (2019)"), creates a folder for it, and then passes 
#    that clean folder to the 'organize_and_rename' engine for episode sorting.
#
# 2. KEY FEATURES:
#    - Heuristic File Grouping: Can separate 'The.Office' from 'Breaking.Bad' 
#      even if they are in the exact same folder.
#    - API Title Sanitization: Connects to TVMaze to ensure the folder name is 
#      Plex-compliant (including the release year).
#    - Handoff Architecture: Perfectly integrates with 'file_manager.py' so 
#      the user doesn't have to manually sort shows into folders first.
#
# 3. APPLICATIONS:
#    - Automated media server management (Plex/Jellyfin/Emby).
#    - Cleaning up large torrent or download dump directories.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - Heavy I/O dependency: Moving massive 4K video files between folders 
#      can take time depending on the user's hard drive speed (HDD vs NVMe).
#    - API Rate Limiting: Uses a timeout on requests to prevent hanging.
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - Movie Parsing: Currently, it ignores movies. It should be updated to 
#      connect to TMDB and sort movies into a separate `/Movies/` directory.
#
# ==============================================================================
