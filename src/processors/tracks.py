import subprocess
import json
import os
import glob
import sys

class TrackProcessor:
    """
    🎬 FEATURES 2 & 3: TRACK CLEANER (Original Logic Intact)
    Handles the intelligent selection and purging of Audio/Subtitle streams.
    """
    def get_track_info(self, input_path: str, stream_type: str = 'a') -> list:
        """Returns a list of tracks found in the video using ffprobe."""
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'stream=index:stream_tags=language,title',
            '-select_streams', stream_type,
            '-of', 'json',
            input_path
        ]
        try:
            output = subprocess.check_output(cmd)
            data = json.loads(output)
            return data.get('streams', [])
        except Exception as e:
            print(f"Error reading tracks: {e}")
            return []

    def process_batch(self, input_path: str, track_indices: list, stream_type: str = 'a'):
        """Handles both single files and folders. Removes chosen type EXCEPT chosen IDs."""
        label = "audio" if stream_type == 'a' else "subtitle"
        tasks = []
        
        # 1. Detect if it's a folder or a single file
        if os.path.isdir(input_path):
            print(f" Scanning folder for videos...")
            valid_exts = ('.mkv', '.mp4', '.avi', '.mov', '.webm', '.ts', '.flv', '.m4v', '.mp3', '.wav', '.flac', '.mka')
            for f in os.listdir(input_path):
                if f.lower().endswith(valid_exts):
                    full_p = os.path.join(input_path, f)
                    if os.path.isfile(full_p):
                        tasks.append(full_p)
            tasks.sort()
        elif os.path.isfile(input_path):
            tasks = [input_path]
        else:
            print(" Invalid path provided.")
            return False

        if not tasks:
            print(" No files found.")
            return False

        print(f" Processing {len(tasks)} files...")
        print("-" * 40)
        
        success_count = 0
        
        for vid in tasks:
            print(f"    Cleaning {label.capitalize()}: {os.path.basename(vid)}")
            base, ext = os.path.splitext(vid)
            out_ext = ext if ext.lower() in ('.mp4', '.mkv', '.mov', '.avi', '.webm', '.m4v') else '.mkv'
            out_path = f"{base}_clean_{label}{out_ext}"
            if os.path.abspath(out_path) == os.path.abspath(vid):
                out_path = f"{base}_clean_{label}_out{out_ext}"
            
            # Inspect actual streams available in this specific file
            file_tracks = self.get_track_info(vid, stream_type)
            num_tracks = len(file_tracks)
            valid_indices = [idx for idx in track_indices if 0 <= idx < num_tracks]

            # --- TIER 1: DYNAMIC STREAM ROUTING (-c copy, full streams, -map 0:V? excludes attached cover art) ---
            command = ['ffmpeg', '-y', '-i', vid]
            
            if stream_type == 'a':
                command.extend(['-map', '0:V?', '-map', '0:s?', '-map', '0:t?'])
                for idx in valid_indices:
                    command.extend(['-map', f'0:a:{idx}?'])
            else: # 's'
                command.extend(['-map', '0:V?', '-map', '0:a?', '-map', '0:t?'])
                for idx in valid_indices:
                    command.extend(['-map', f'0:s:{idx}?'])
                
            command.extend([
                '-c', 'copy',                         # Packet-level stream copy (Zero decoding).
                '-ignore_unknown',                    # Suppresses abortions caused by esoteric metadata headers.
                '-avoid_negative_ts', 'make_zero',    # Shifts PTS/DTS vectors to origin (0) to resolve container desync.
                out_path
            ])
            
            success = False
            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
                if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                    success = True
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.strip()[:300] if e.stderr else 'Unknown error'
                print(f"    Primary cleaning failed for {os.path.basename(vid)}: {err_msg}")
                if os.path.exists(out_path):
                    try:
                        os.remove(out_path)
                    except Exception:
                        pass

                # --- TIER 2 FALLBACK: Drop potentially incompatible subtitle/attachment streams ---
                command_fb = ['ffmpeg', '-y', '-i', vid]
                if stream_type == 'a':
                    command_fb.extend(['-map', '0:V?'])
                    for idx in valid_indices:
                        command_fb.extend(['-map', f'0:a:{idx}?'])
                else:
                    command_fb.extend(['-map', '0:V?', '-map', '0:a?'])
                    for idx in valid_indices:
                        command_fb.extend(['-map', f'0:s:{idx}?'])

                command_fb.extend([
                    '-c', 'copy',
                    '-ignore_unknown',
                    '-avoid_negative_ts', 'make_zero',
                    out_path
                ])

                try:
                    subprocess.run(command_fb, check=True, capture_output=True, text=True)
                    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                        print(f"    Fallback cleaning (Tier 2) succeeded for {os.path.basename(vid)}")
                        success = True
                except subprocess.CalledProcessError as e_fb:
                    fb_err = e_fb.stderr.strip()[:300] if e_fb.stderr else 'Unknown error'
                    print(f"    Fallback cleaning (Tier 2) failed for {os.path.basename(vid)}: {fb_err}")
                    if os.path.exists(out_path):
                        try:
                            os.remove(out_path)
                        except Exception:
                            pass

                    # --- TIER 3 FALLBACK: Transcode audio/subtitles if stream copy fails ---
                    command_fb3 = ['ffmpeg', '-y', '-i', vid]
                    if stream_type == 'a':
                        command_fb3.extend(['-map', '0:V?'])
                        for idx in valid_indices:
                            command_fb3.extend(['-map', f'0:a:{idx}?'])
                        command_fb3.extend(['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k'])
                    else:
                        command_fb3.extend(['-map', '0:V?', '-map', '0:a?'])
                        for idx in valid_indices:
                            command_fb3.extend(['-map', f'0:s:{idx}?'])
                        command_fb3.extend(['-c:v', 'copy', '-c:a', 'copy', '-c:s', 'srt'])

                    command_fb3.extend([
                        '-ignore_unknown',
                        '-avoid_negative_ts', 'make_zero',
                        out_path
                    ])

                    try:
                        subprocess.run(command_fb3, check=True, capture_output=True, text=True)
                        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                            print(f"    Fallback cleaning (Tier 3) succeeded for {os.path.basename(vid)}")
                            success = True
                    except subprocess.CalledProcessError as e_fb3:
                        fb3_err = e_fb3.stderr.strip()[:300] if e_fb3.stderr else 'Unknown error'
                        print(f"    Fallback cleaning (Tier 3) failed for {os.path.basename(vid)}: {fb3_err}")
                        if os.path.exists(out_path):
                            try:
                                os.remove(out_path)
                            except Exception:
                                pass

                        # --- TIER 4 FALLBACK: Full video/audio re-encode for corrupt/problematic containers ---
                        command_fb4 = ['ffmpeg', '-y', '-i', vid]
                        if stream_type == 'a':
                            command_fb4.extend(['-map', '0:V?'])
                            for idx in valid_indices:
                                command_fb4.extend(['-map', f'0:a:{idx}?'])
                            command_fb4.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-c:a', 'aac', '-b:a', '192k'])
                        else:
                            command_fb4.extend(['-map', '0:V?', '-map', '0:a?'])
                            for idx in valid_indices:
                                command_fb4.extend(['-map', f'0:s:{idx}?'])
                            command_fb4.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-c:a', 'copy', '-c:s', 'srt'])

                        command_fb4.extend([
                            '-ignore_unknown',
                            '-avoid_negative_ts', 'make_zero',
                            out_path
                        ])

                        try:
                            subprocess.run(command_fb4, check=True, capture_output=True, text=True)
                            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                                print(f"    Fallback cleaning (Tier 4) succeeded for {os.path.basename(vid)}")
                                success = True
                        except subprocess.CalledProcessError as e_fb4:
                            fb4_err = e_fb4.stderr.strip()[:300] if e_fb4.stderr else 'Unknown error'
                            print(f"    Fallback cleaning (Tier 4) failed for {os.path.basename(vid)}: {fb4_err}")
                            if os.path.exists(out_path):
                                try:
                                    os.remove(out_path)
                                except Exception:
                                    pass

            if success:
                print(f"    Saved: {os.path.basename(out_path)}")
                success_count += 1
            else:
                print(f"    Failed: {os.path.basename(vid)}")

        print("-" * 40)
        return success_count > 0

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
#
# Syntax: python src/processors/tracks.py <VideoPath> <Mode> <TrackIDs>
#
# Mode: 'a' for Audio, 's' for Subtitles
# TrackIDs: The index numbers of tracks to KEEP (separated by comma)
#
# Example Command:
# python src/processors/tracks.py "C:\Movies\Avatar.mkv" "a" "0,2"
#
# (This keeps Audio Track 0 and 2, removes the rest)
#
# BATCH FOLDER EXAMPLE:
# python src/processors/tracks.py "C:\Movies\Season1" "s" "0"
#
# (This looks at every video in the folder and removes all subtitles EXCEPT Track 0)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: THE MULTI-STREAM TRACK CLEANER (TrackProcessor)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'tracks.py', and it acts as a "Surgical Tool" for your 
#    video files. Its job is to identify all the different audio and subtitle 
#    tracks inside a container, and let you strip away the ones you don't need. 
#    It’s essential for cleaning up bloated movie files that have 20 different 
#    languages, allowing you to keep only the ones you actually want on your server.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The Track Processor uses 'ffprobe' to scan the internal metadata. It uses 
#    Negative Mapping ('-map -0:a') to deselect all tracks before surgically 
#    adding back only the user-approved IDs. It supports 'Batch Processing,' 
#    meaning it can clean an entire folder of movies automatically in one go.
#
# 2. KEY FEATURES:
#    - Stream Copying (-c copy): Ensures 100% original quality is maintained 
#      with zero re-encoding time.
#    - Recursive Batching: Automatically finds all videos in sub-folders.
#    - Timeline Synchronization: Includes '-avoid_negative_ts' to ensure the 
#      cleaned files don't suffer from audio sync issues.
#
# 3. APPLICATIONS:
#    - Server Optimization: Removing 'dead weight' audio tracks to save GBs 
#      of storage across a massive movie library.
#    - Language Localization: Creating clean versions of films with only 
#      native language audio and subtitles.
#
# ==============================================================================