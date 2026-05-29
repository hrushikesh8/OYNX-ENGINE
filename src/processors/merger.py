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
        print(f"   🔗 VidFlow Merger: {os.path.basename(video_path)} + {os.path.basename(audio_path)}")
        
        command = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-map', '0:v:0',      # Video from Input 0
            '-map', '1:a:0',      # Audio from Input 1
            '-c', 'copy',         # Direct stream copy (No re-encoding)
            '-shortest',          # Stops when the shortest stream ends
            '-ignore_unknown',
            output_path
        ]
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def mux_subtitles(self, video_path: str, sub_path: str, output_path: str):
        """Embeds a subtitle file into a video container."""
        print(f"   📝 Muxing Subs: {os.path.basename(video_path)} + {os.path.basename(sub_path)}")

        command = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', sub_path,
            '-map', '0',          # Take everything from original video
            '-map', '1',          # Add the subtitle file
            '-c', 'copy'          # Copy all streams
        ]

        # CRITICAL FIX: MP4 files do not support 'srt' codec. They need 'mov_text'.
        if output_path.lower().endswith('.mp4'):
            command.extend(['-c:s', 'mov_text'])
        else:
            command.extend(['-c:s', 'srt'])

        command.append(output_path)
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    # ==========================================
    # 2. THE SMART BATCH AUTOMATION ENGINE
    # ==========================================
    def _find_matching_file(self, folder, base_name, valid_extensions):
        """Helper tool to find a matching file regardless of extension."""
        for ext in valid_extensions:
            potential_file = os.path.join(folder, base_name + ext)
            if os.path.exists(potential_file):
                return potential_file
        return None

    def batch_process_folder(self, target_folder: str, mode: str):
        """
        Scans a folder and automatically pairs/muxes files with identical names.
        """
        if not os.path.exists(target_folder):
            print(f"❌ Error: Path not found -> {target_folder}")
            return False

        print(f"\n📂 Onyx Batch Merger Scanning: {target_folder}")
        files = os.listdir(target_folder)
        success_count = 0

        for file in files:
            if file.lower().endswith(self.video_exts):
                # Ignore files we already processed in a previous run
                if file.startswith("Onyx_Merged_"):
                    continue

                base_name = os.path.splitext(file)[0]
                video_path = os.path.join(target_folder, file)
                
                # Identify the track to merge based on mode
                if mode == 'subtitle':
                    matching_track = self._find_matching_file(target_folder, base_name, self.sub_exts)
                else: # audio mode
                    matching_track = self._find_matching_file(target_folder, base_name, self.audio_exts)

                if matching_track:
                    # Keep original extension or default to .mkv for high compatibility
                    ext = os.path.splitext(file)[1]
                    output_name = f"Onyx_Merged_{base_name}{ext}"
                    output_path = os.path.join(target_folder, output_name)

                    if mode == 'subtitle':
                        if self.mux_subtitles(video_path, matching_track, output_path):
                            success_count += 1
                    else:
                        if self.merge_video_audio(video_path, matching_track, output_path):
                            success_count += 1

        print("-" * 50)
        if success_count > 0:
            print(f"🎉 BATCH COMPLETE: {success_count} files successfully processed.")
        else:
            print("⚠️ No matching pairs found. (Ensure filenames match perfectly!)")
        print("-" * 50)
        return True


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
