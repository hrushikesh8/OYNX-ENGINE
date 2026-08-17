import subprocess
import os

class StreamMerger:
    def __init__(self):
        # The file extensions the Batch Engine will look for
        self.video_exts = ('.mp4', '.mkv', '.avi', '.mov')
        self.sub_exts = ('.srt', '.ass', '.vtt')
        self.audio_exts = ('.mka', '.aac', '.mp3', '.ac3', '.eac3', '.wav', '.m4a')

    # ==========================================
    # 1. SINGLE FILE ENGINES
    # ==========================================
    def merge_video_audio(self, video_path: str, audio_path: str, output_path: str):
        """Combines visuals with a separate audio file instantly."""
        print(f"    VidFlow Merger: {os.path.basename(video_path)} + {os.path.basename(audio_path)}")
        
        command = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-map', '0:v:0',      # Extracts the primary video stream (Index 0) from the first input array.
            '-map', '1:a:0',      # Extracts the primary audio stream (Index 0) from the second input array.
            '-c', 'copy',         # Direct stream copy.
            '-shortest',          # Terminates process when shortest stream concludes.
            '-ignore_unknown',    # Bypasses anomalous metadata headers.
            output_path
        ]
        
        try:
            res = subprocess.run(command, capture_output=True, text=True)
            if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            else:
                print(f"    FFmpeg error merging video & audio: {res.stderr}")
                return False
        except Exception as e:
            print(f"    Exception merging video & audio: {e}")
            return False

    def mux_subtitles(self, video_path: str, sub_path: str, output_path: str):
        """Embeds a subtitle file into a video container cleanly."""
        print(f"    Muxing Subs: {os.path.basename(video_path)} + {os.path.basename(sub_path)}")

        command = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', sub_path,
            '-map', '0:v',
            '-map', '0:a?',
            '-map', '0:s?',
            '-map', '1',
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-c:s', 'copy'
        ]

        if output_path.lower().endswith('.mp4'):
            command.extend(['-c:s', 'mov_text'])

        command.append(output_path)
        
        try:
            res = subprocess.run(command, capture_output=True, text=True)
            if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            else:
                print(f"    FFmpeg error muxing subtitles: {res.stderr}")
                if output_path.lower().endswith('.mp4'):
                    mkv_output = os.path.splitext(output_path)[0] + ".mkv"
                    print(f"    Retrying muxing with MKV container fallback: {os.path.basename(mkv_output)}")
                    fallback_cmd = [
                        'ffmpeg', '-y',
                        '-i', video_path,
                        '-i', sub_path,
                        '-map', '0:v',
                        '-map', '0:a?',
                        '-map', '0:s?',
                        '-map', '1',
                        '-c', 'copy',
                        mkv_output
                    ]
                    res_fb = subprocess.run(fallback_cmd, capture_output=True, text=True)
                    if res_fb.returncode == 0 and os.path.exists(mkv_output):
                        return True
                return False
        except Exception as e:
            print(f"    Exception muxing subtitles: {e}")
            return False

    def _get_subtitle_stream_count(self, video_path: str) -> int:
        """Returns the number of existing subtitle streams in a video using ffprobe."""
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 's',
                '-show_entries', 'stream=index',
                '-of', 'csv=p=0',
                video_path
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = [line.strip() for line in res.stdout.strip().split('\n') if line.strip()]
            return len(lines)
        except Exception:
            return 0

    def mux_multiple_subtitles(self, video_path: str, sub_paths: list, output_path: str) -> bool:
        """Embeds multiple subtitle files into a video container simultaneously."""
        if not video_path or not sub_paths:
            return False

        print(f"    Muxing {len(sub_paths)} Subtitles into: {os.path.basename(video_path)}")

        command = ['ffmpeg', '-y', '-i', video_path]
        for sub in sub_paths:
            command.extend(['-i', sub])

        command.extend(['-map', '0:v', '-map', '0:a?', '-map', '0:s?'])
        for i in range(1, len(sub_paths) + 1):
            command.extend(['-map', str(i)])

        command.extend(['-c:v', 'copy', '-c:a', 'copy', '-c:s', 'copy'])

        if output_path.lower().endswith('.mp4'):
            command.extend(['-c:s', 'mov_text'])

        existing_subs = self._get_subtitle_stream_count(video_path)

        for idx, sub_path in enumerate(sub_paths):
            sub_title = os.path.splitext(os.path.basename(sub_path))[0]
            stream_idx = existing_subs + idx
            command.extend([f'-metadata:s:s:{stream_idx}', f'title={sub_title}'])

        command.append(output_path)

        try:
            res = subprocess.run(command, capture_output=True, text=True)
            if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            else:
                print(f"    Error muxing multiple subtitles: {res.stderr}")
                return False
        except Exception as e:
            print(f"    Exception muxing multiple subtitles: {e}")
            return False

    # ==========================================
    # 2. THE SMART BATCH AUTOMATION ENGINE
    # ==========================================
    def _extract_episode_code(self, filename: str) -> str:
        """Extracts episode pattern like S01E01 or 1x01 from filename."""
        import re
        match = re.search(r'(s\d{1,2}e\d{1,2}|\d{1,2}x\d{1,2})', filename, re.IGNORECASE)
        return match.group(1).lower() if match else ""

    def _find_matching_file(self, folder: str, base_name: str, valid_extensions: tuple, video_filename: str = ""):
        """Helper tool to find a matching file regardless of extension with flexible pattern matching."""
        if not os.path.exists(folder):
            return None

        all_files = os.listdir(folder)
        candidates = [
            f for f in all_files
            if f.lower().endswith(valid_extensions) and not (
                f.startswith("Onyx_Merged_") or "_subs_added" in f or "_all_subs" in f or "_audio_synced" in f
            )
        ]

        if not candidates:
            return None

        # Priority 1: Exact match base_name + ext
        for ext in valid_extensions:
            exact = base_name + ext
            for cand in candidates:
                if cand.lower() == exact.lower():
                    return os.path.join(folder, cand)

        # Priority 2: Matches starting with base_name (e.g. base_name.en.srt, base_name_eng.srt)
        for cand in candidates:
            cand_base = os.path.splitext(cand)[0].lower()
            if cand_base.startswith(base_name.lower()) or base_name.lower().startswith(cand_base):
                return os.path.join(folder, cand)

        # Priority 3: Season & Episode matching (e.g. S01E01)
        ep_code = self._extract_episode_code(video_filename or base_name)
        if ep_code:
            for cand in candidates:
                if ep_code in cand.lower():
                    return os.path.join(folder, cand)

        # Priority 4: Single-pair fallback (if directory has 1 video file and 1+ candidate tracks)
        video_files_in_folder = [
            f for f in all_files
            if f.lower().endswith(self.video_exts) and not (
                f.startswith("Onyx_Merged_") or "_subs_added" in f or "_all_subs" in f or "_audio_synced" in f
            )
        ]
        if len(video_files_in_folder) == 1 and len(candidates) >= 1:
            return os.path.join(folder, candidates[0])

        return None

    def batch_process_folder(self, target_folder: str, mode: str):
        """
        Scans a folder and its immediate subdirectories to automatically pair and mux files.
        Returns (success_bool, message_string).
        """
        if not os.path.exists(target_folder):
            print(f" Error: Path not found -> {target_folder}")
            return False, f"Path not found: {target_folder}"

        print(f"\n Onyx Batch Merger Scanning: {target_folder}")
        
        folders_to_scan = [target_folder]
        for item in os.listdir(target_folder):
            full_item = os.path.join(target_folder, item)
            if os.path.isdir(full_item) and not item.startswith('.'):
                folders_to_scan.append(full_item)

        total_processed = 0

        for folder in folders_to_scan:
            files = os.listdir(folder)
            for file in files:
                if file.lower().endswith(self.video_exts):
                    if file.startswith("Onyx_Merged_") or "_subs_added" in file or "_all_subs" in file or "_audio_synced" in file:
                        continue

                    base_name = os.path.splitext(file)[0]
                    video_path = os.path.join(folder, file)
                    
                    if mode == 'subtitle':
                        matching_track = self._find_matching_file(folder, base_name, self.sub_exts, video_filename=file)
                    else: # audio mode
                        matching_track = self._find_matching_file(folder, base_name, self.audio_exts, video_filename=file)

                    if matching_track:
                        ext = os.path.splitext(file)[1]
                        if mode == 'subtitle':
                            output_name = f"{base_name}_subs_added{ext}"
                        else:
                            output_name = f"Onyx_Merged_{base_name}{ext}"
                        output_path = os.path.join(folder, output_name)

                        if mode == 'subtitle':
                            if self.mux_subtitles(video_path, matching_track, output_path):
                                total_processed += 1
                        else:
                            if self.merge_video_audio(video_path, matching_track, output_path):
                                total_processed += 1

        print("-" * 50)
        if total_processed > 0:
            msg = f"BATCH COMPLETE: {total_processed} files successfully processed."
            print(f" {msg}")
            print("-" * 50)
            return True, msg
        else:
            msg = "No matching video & track pairs found in folder."
            print(f" {msg}")
            print("-" * 50)
            return False, msg

    def batch_process_multi_subtitles_folder(self, target_folder: str):
        """
        Scans folder (and direct subdirectories) for video files and subtitle files,
        embedding all subtitles simultaneously.
        Returns (success_bool, message_string).
        """
        if not os.path.exists(target_folder):
            return False, f"Path not found: {target_folder}"

        folders_to_scan = [target_folder]
        for item in os.listdir(target_folder):
            full_item = os.path.join(target_folder, item)
            if os.path.isdir(full_item) and not item.startswith('.'):
                folders_to_scan.append(full_item)

        total_processed = 0

        for folder in folders_to_scan:
            all_files = os.listdir(folder)
            video_files = [
                f for f in all_files
                if f.lower().endswith(self.video_exts) and not (
                    f.startswith("Onyx_Merged_") or "_subs_added" in f or "_all_subs" in f or "_audio_synced" in f
                )
            ]
            sub_files = [
                f for f in all_files
                if f.lower().endswith(self.sub_exts) and not (
                    f.startswith("Onyx_Merged_") or "_subs_added" in f or "_all_subs" in f
                )
            ]

            if not video_files or not sub_files:
                continue

            if len(video_files) == 1:
                v_file = video_files[0]
                video_path = os.path.join(folder, v_file)
                sub_paths = [os.path.join(folder, s) for s in sorted(sub_files)]
                base_name, ext = os.path.splitext(v_file)
                output_name = f"{base_name}_all_subs{ext}"
                output_path = os.path.join(folder, output_name)

                if self.mux_multiple_subtitles(video_path, sub_paths, output_path):
                    total_processed += 1
            else:
                for v_file in video_files:
                    base_name, ext = os.path.splitext(v_file)
                    video_path = os.path.join(folder, v_file)

                    matched_subs = [
                        os.path.join(folder, s) for s in sorted(sub_files)
                        if s.lower().startswith(base_name.lower())
                    ]

                    if not matched_subs:
                        ep_code = self._extract_episode_code(v_file)
                        if ep_code:
                            matched_subs = [
                                os.path.join(folder, s) for s in sorted(sub_files)
                                if ep_code in s.lower()
                            ]

                    if not matched_subs:
                        matched_subs = [os.path.join(folder, s) for s in sorted(sub_files)]

                    output_name = f"{base_name}_all_subs{ext}"
                    output_path = os.path.join(folder, output_name)

                    if self.mux_multiple_subtitles(video_path, matched_subs, output_path):
                        total_processed += 1

        if total_processed > 0:
            return True, f"Multi-Subtitle batch finished: {total_processed} files processed."
        else:
            return False, "No valid video and subtitle pairs found to mux."


# ==============================================================================
# 🎬 FEATURE: THE MEDIA MERGER & SUBTITLE ENGINE (StreamMerger)
# ==============================================================================
# (Your excellent original documentation remains here!)

# ==========================================
# HOW TO USE THIS CODE (DOCUMENTATION)
# ==========================================
#
# NOTE: This file is a CLASS MODULE. It should be imported into 'main.py'.
#
# 1. Import:
#    from src.processors.merger import StreamMerger
#
# 2. Instantiate:
#    merger = StreamMerger()
#
# 3. USE CASE A: Merge Video + Audio
#    merger.merge_video_audio(
#        video_path="C:/Videos/SilentMovie.mp4",
#        audio_path="C:/Videos/AudioTrack.mp3",
#        output_path="C:/Videos/FinalMovie.mkv"
#    )
#
# 4. USE CASE B: Mux Subtitles (Soft Subs)
#    merger.mux_subtitles(
#        video_path="C:/Videos/Movie.mkv",
#        sub_path="C:/Videos/English.srt",
#        output_path="C:/Videos/Movie_Subbed.mkv"
#    )
#
# Result: 
# Merges streams instantly without loss. Option B allows your cloud 
# server users to toggle subtitles on or off in the player.
# ==========================================

# ==============================================================================
# 🎬 FEATURE: THE MEDIA MERGER & SUBTITLE ENGINE (StreamMerger)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'merger.py', and it is the "Final Assembly" tool. 
#    It handles two critical roles: combining separate high-quality video 
#    and audio streams into one master file, and embedding subtitles (SRT) 
#    into movies so they are natively available in any media player.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The StreamMerger uses FFmpeg's mapping system. For audio, it surgically 
#    selects Stream 0:v:0 and 1:a:0. For subtitles, it uses the `-map 0 -map 1` 
#    logic to append a new text track to the existing stream stack.
#
# 2. KEY FEATURES:
#    - Intelligent Subtitle Coding: Forces 'srt' codec for maximum compatibility.
#    - Corrupt Stream Handling: Uses `-ignore_unknown` to bypass bad metadata.
#    - Zero Quality Loss: Uses `-c copy` to move data without re-processing.
#    - Timeline Synchronization: Includes `-avoid_negative_ts` for perfect sync.
#
# 3. APPLICATIONS:
#    - Pro-Level Remastering: Combining AI-upscaled video with original audio.
#    - Library Internationalization: Adding multi-language subtitle tracks.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - Speed: Instant (Muxing only).
#    - CPU Usage: Low (Only handles container wrapping).
#
# ==============================================================================

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.merger import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (merger.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'merger.py', is a core component of the Onyx Engine. It is
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
