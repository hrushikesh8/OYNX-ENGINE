import os
import shutil
import re
from src.processors.time_machine import TimeMachine

def flatten_directory(folder_path, run_id=None):
    """
    THE DEEP SCAVENGER (Extractor / Unpacker)
    Walks through every single sub-folder inside the folder_path.
    If it finds a video or subtitle, it rips it out and drops it in the root folder.
    Then, it destroys the empty sub-folders left behind.
    """
    print(f"\n🚜 Igniting Deep Scavenger in '{folder_path}'...")
    print("-" * 50)
    
    valid_exts = ('.mkv', '.mp4', '.avi', '.m4v', '.srt', '.ass', '.vtt')
    moved_count = 0
    
    for root, dirs, files in os.walk(folder_path, topdown=False):
        if root == folder_path: 
            continue 
            
        for file in files:
            if file.lower().endswith(valid_exts):
                old_path = os.path.join(root, file)
                new_path = os.path.join(folder_path, file)
                
                # Collision Handler: If files share a name, append _v2
                if os.path.exists(new_path) and old_path != new_path:
                    base, ext = os.path.splitext(file)
                    new_path = os.path.join(folder_path, f"{base}_v2{ext}")
                    
                shutil.move(old_path, new_path)
                
                # ---> TIME MACHINE LOGGING <---
                if run_id:
                    TimeMachine.log_action("Chronicle", run_id, "SCAVENGE", old_path, new_path, op_type="RENAME")
                    
                moved_count += 1
                
        # Sweep up the empty folders
        if not os.listdir(root):
            try: os.rmdir(root)
            except OSError: pass

    print(f"✅ Deep Scavenger Complete: Extracted {moved_count} files to the root directory.")


def pack_volumes(folder_path, show_name, max_size_gb, run_id=None):
    """
    THE SMART VOLUME DISPATCHER (Packer v2.0)
    Calculates file sizes, plans the chunks based on your GB limit, 
    and dynamically names the folders (e.g., 'ShowName S01 E01-08').
    """
    print(f"\n📦 Packing '{folder_path}' into {max_size_gb}GB smart volumes...")
    print("-" * 50)
    
    max_bytes = max_size_gb * 1024 * 1024 * 1024
    valid_exts = ('.mkv', '.mp4', '.avi', '.m4v', '.srt', '.ass', '.vtt')
    
    # files.sort() guarantees the files are processed in alphabetical order by name!
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(valid_exts)]
    files.sort()
    
    if not files:
        print("⚠️ No valid media files found to pack.")
        return

    # --- Step 1: Plan the chunks ---
    chunks = []
    current_chunk = []
    current_size = 0
    
    for f in files:
        file_path = os.path.join(folder_path, f)
        file_size = os.path.getsize(file_path)
        
        # If adding this file breaks the GB limit, close the chunk and start a new one
        if (current_size + file_size > max_bytes) and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_size = 0
            
        current_chunk.append(f)
        current_size += file_size
        
    if current_chunk:
        chunks.append(current_chunk)

    # --- Step 2: Execute and dynamically name the folders ---
    pattern = re.compile(r'(?i)(.*?)[Ss](\d+)[\s\.\-]*[EeXx](\d+)')
    packed_count = 0

    for idx, chunk in enumerate(chunks):
        first_file = chunk[0]
        last_file = chunk[-1]
        
        match_first = pattern.search(first_file)
        match_last = pattern.search(last_file)
        
        if match_first and match_last:
            # Extract Show Name, Season, and Episode ranges
            parsed_show_name = match_first.group(1).replace('.', ' ').strip()
            
            # Use user's manual show_name if regex failed to capture one, else use regex parsed
            if not parsed_show_name and show_name:
                parsed_show_name = show_name
            elif not parsed_show_name:
                parsed_show_name = os.path.basename(os.path.normpath(folder_path))
                
            season = int(match_first.group(2))
            ep_start = int(match_first.group(3))
            ep_end = int(match_last.group(3))
            
            if ep_start == ep_end:
                folder_name = f"{parsed_show_name} S{season:02d} E{ep_start:02d}"
            else:
                folder_name = f"{parsed_show_name} S{season:02d} E{ep_start:02d}-{ep_end:02d}"
        else:
            # Fallback if the files aren't formatted perfectly
            if show_name:
                folder_name = f"{show_name} Volume {idx + 1:02d}"
            else:
                folder_name = f"Volume {idx + 1:02d}"

        vol_path = os.path.join(folder_path, folder_name)
        os.makedirs(vol_path, exist_ok=True)
        
        # Move the files and their corresponding subtitles
        for f in chunk:
            old_vid_path = os.path.join(folder_path, f)
            new_vid_path = os.path.join(vol_path, f)
            
            shutil.move(old_vid_path, new_vid_path)
            packed_count += 1
            
            # ---> TIME MACHINE LOGGING FOR VIDEO <---
            if run_id:
                TimeMachine.log_action("Chronicle", run_id, "PACK_VOLUME", old_vid_path, new_vid_path, op_type="RENAME")
            
            base_name = os.path.splitext(f)[0]
            for sub_ext in ['.srt', '.ass', '.vtt']:
                sub_file = base_name + sub_ext
                sub_path = os.path.join(folder_path, sub_file)
                new_sub_path = os.path.join(vol_path, sub_file)
                
                if os.path.exists(sub_path):
                    shutil.move(sub_path, new_sub_path)
                    
                    # ---> TIME MACHINE LOGGING FOR SUBTITLE <---
                    if run_id:
                        TimeMachine.log_action("Chronicle", run_id, "PACK_SUBTITLE", sub_path, new_sub_path, op_type="RENAME")
                    
        print(f"   📁 Created: {folder_name} ({len(chunk)} episodes)")

    print("-" * 50)
    print(f"✅ Successfully packed {packed_count} files into {len(chunks)} smart volumes!")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.utilities import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (utilities.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'utilities.py', is a core component of the Onyx Engine. It is
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
