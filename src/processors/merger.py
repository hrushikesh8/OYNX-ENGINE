import subprocess
import os

class StreamMerger:
    def __init__(self):
        # The file extensions the Batch Engine will look for
        self.video_exts = ('.mp4', '.mkv', '.avi', '.mov')
        self.sub_exts = ('.srt', '.ass', '.vtt')
        self.audio_exts = ('.mka', '.aac', '.mp3', '.ac3', '.eac3', '.wav', '.m4a')

    # ==========================================
    # 1. SINGLE FILE ENGINES (Your Original Perfect Code)
    # ==========================================
    def merge_video_audio(self, video_path: str, audio_path: str, output_path: str):
        """
        Combines a video file (visuals) with a separate audio file.
        Useful when you have downloaded 'Video Only' and 'Audio Only' streams separately.
        """
        """Combines a video file (visuals) with a separate audio file."""
        print(f"   🔗 VidFlow Merger: {os.path.basename(video_path)} + {os.path.basename(audio_path)}")
        
        command = [
            'ffmpeg',
            '-i', video_path,   # Input 0: The Video File
            '-i', audio_path,   # Input 1: The Audio File
            '-c:v', 'copy',     # Copy video stream directly
            '-c:a', 'copy',     # Copy audio stream directly
            '-map', '0:v:0',    # Take the 1st Video stream from Input 0
            '-map', '1:a:0',    # Take the 1st Audio stream from Input 1
            '-ignore_unknown',  # Skip corrupt streams
            '-avoid_negative_ts', 'make_zero', 
            '-y', output_path
        ]
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"   ✅ Success: {os.path.basename(output_path)}")
            return True
        except subprocess.CalledProcessError:
            print(f"   ❌ Merge Failed for: {os.path.basename(video_path)}")
            return False

    def mux_subtitles(self, video_path: str, sub_path: str, output_path: str):
        """Embeds (Softcodes) a subtitle file into a video container."""
        print(f"   🔗 Muxing Subs: {os.path.basename(video_path)} + {os.path.basename(sub_path)}")

        command = [
            'ffmpeg', '-i', video_path, '-i', sub_path,
            '-map', '0',   # Take EVERYTHING from Input 0
            '-map', '1',   # ADD the new subtitle file
            '-c', 'copy',  # Copy everything
            '-c:s', 'srt', # Force SRT codec
            '-ignore_unknown', 
            '-avoid_negative_ts', 'make_zero', 
            '-y', output_path
        ]
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"   ✅ Success: {os.path.basename(output_path)}")
            return True
        except subprocess.CalledProcessError:
            print(f"   ❌ Mux Error for: {os.path.basename(video_path)}")
            return False

    # ==========================================
    # 2. THE NEW BATCH AUTOMATION ENGINE
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
        Scans a folder and automatically pairs/muxes files.
        mode can be 'audio' or 'subtitle'
        """
        if not os.path.exists(target_folder):
            print(f"❌ Error: Path not found -> {target_folder}")
            return False

        print(f"📂 Batch Merger Scanning: {target_folder}")
        files = os.listdir(target_folder)
        success_count = 0

        for file in files:
            if file.lower().endswith(self.video_exts):
                base_name = os.path.splitext(file)[0]
                video_path = os.path.join(target_folder, file)
                
                if mode == 'subtitle':
                    matching_track = self._find_matching_file(target_folder, base_name, self.sub_exts)
                elif mode == 'audio':
                    matching_track = self._find_matching_file(target_folder, base_name, self.audio_exts)

                if matching_track:
                    output_name = f"{base_name}_Muxed.mkv"
                    output_path = os.path.join(target_folder, output_name)

                    # Feed it to your original, perfect single-file functions!
                    if mode == 'subtitle':
                        if self.mux_subtitles(video_path, matching_track, output_path):
                            success_count += 1
                    elif mode == 'audio':
                        if self.merge_video_audio(video_path, matching_track, output_path):
                            success_count += 1

        print("-" * 50)
        if success_count > 0:
            print(f"🎉 BATCH COMPLETE: {success_count} files successfully muxed.")
        else:
            print("⚠️ No matching pairs found. (Make sure video and track names match perfectly!)")
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