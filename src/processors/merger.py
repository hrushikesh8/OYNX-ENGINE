import subprocess
import os

class StreamMerger:
    def merge_video_audio(self, video_path: str, audio_path: str, output_path: str):
        """
        Combines a video file (visuals) with a separate audio file.
        Useful when you have downloaded 'Video Only' and 'Audio Only' streams separately.
        """
        print(f"   🔗 VidFlow Merger: {os.path.basename(video_path)} + {os.path.basename(audio_path)}")
        
        command = [
            'ffmpeg',
            '-i', video_path,   # Input 0: The Video File
            '-i', audio_path,   # Input 1: The Audio File
            
            # --- CODEC SETTINGS ---
            '-c:v', 'copy',     # Copy video stream directly (No quality loss)
            '-c:a', 'copy',     # Copy audio stream directly
            
            # --- MAPPING (The Crucial Part) ---
            '-map', '0:v:0',    # Take the 1st Video stream from Input 0
            '-map', '1:a:0',    # Take the 1st Audio stream from Input 1
            
            # --- SAFETY & SERVER FLAGS ---
            '-ignore_unknown',  # Skip corrupt streams instead of crashing
            '-avoid_negative_ts', 'make_zero', # 🚀 UPGRADE: Perfect for cloud server sync
            
            '-y', output_path   # Overwrite output file
        ]
        
        try:
            subprocess.run(command, check=True, capture_output=True)
            print(f"   ✅ Success: {os.path.basename(output_path)}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Merge Failed: {e.stderr.decode('utf-8')}")
            return False

    def mux_subtitles(self, video_path: str, sub_path: str, output_path: str):
        """
        Embeds (Softcodes) a subtitle file into a video container.
        The subtitles can be turned on/off by the player.
        """
        print(f"   🔗 Muxing Subs: {os.path.basename(video_path)} + {os.path.basename(sub_path)}")

        command = [
            'ffmpeg', '-i', video_path, '-i', sub_path,
            
            # --- MAPPING ---
            '-map', '0',   # Take EVERYTHING from Input 0 (Video + Original Audio + Original Subs)
            '-map', '1',   # ADD the new subtitle file as an extra track
            
            # --- CODEC SETTINGS ---
            '-c', 'copy',  # Copy everything
            '-c:s', 'srt', # Force the subtitle codec to be SRT (Most compatible format)
            
            '-ignore_unknown', # Safety against corrupt streams
            '-avoid_negative_ts', 'make_zero', # 🚀 UPGRADE: Ensures subs stay in sync
            '-y', output_path
        ]
        
        try:
            subprocess.run(command, check=True, capture_output=True)
            print(f"   ✅ Success: {os.path.basename(output_path)}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Mux Error: {e.stderr.decode('utf-8')}")
            return False

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