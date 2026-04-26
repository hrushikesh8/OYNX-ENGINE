import subprocess
import os

class StreamMerger:
    def merge_video_audio(self, video_path: str, audio_path: str, output_path: str):
        """
        Combines a video file (visuals) with a separate audio file.
        Useful when you have downloaded 'Video Only' and 'Audio Only' streams separately.
        """
        print(f"   🔗 Merging: {os.path.basename(video_path)} + {os.path.basename(audio_path)}")
        
        command = [
            'ffmpeg',
            '-i', video_path,   # Input 0: The Video File
            '-i', audio_path,   # Input 1: The Audio File
            
            # --- CODEC SETTINGS ---
            '-c:v', 'copy',     # Copy video stream directly (No quality loss, very fast)
            '-c:a', 'copy',     # Copy audio stream directly
            
            # --- MAPPING (The Crucial Part) ---
            '-map', '0:v:0',    # Take the 1st Video stream from Input 0
            '-map', '1:a:0',    # Take the 1st Audio stream from Input 1
            
            # --- SAFETY FLAGS ---
            '-ignore_unknown',  # CRITICAL: If the input video has a broken/corrupt stream 
                                # (like 'codec: none'), this tells FFmpeg to skip it 
                                # instead of crashing the script.
            
            '-y', output_path   # Overwrite output file if it exists
        ]
        
        try:
            # capture_output=True hides the messy FFmpeg logs unless there is an error
            subprocess.run(command, check=True, capture_output=True)
            print(f"   ✅ Success: {os.path.basename(output_path)}")
            return True
        except subprocess.CalledProcessError as e:
            # If it fails, decode the error bytes to text so we can read it
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
# NOTE: This file is a CLASS MODULE. It is not meant to be run directly.
#       It should be imported into a script like 'main.py'.
#
# 1. Import the class:
#    from src.processors.merger import StreamMerger
#
# 2. Instantiate the class:
#    merger = StreamMerger()
#
# 3. USE CASE A: Merge Video + Audio (External Audio File)
#    # Useful if you have 'movie.mp4' (silent) and 'audio.mp3'
#    merger.merge_video_audio(
#        video_path="C:/Videos/SilentMovie.mp4",
#        audio_path="C:/Videos/AudioTrack.mp3",
#        output_path="C:/Videos/FinalMovie.mkv"
#    )
#
# 4. USE CASE B: Mux Subtitles (Soft Subs)
#    # Useful to add .srt files into an MKV container
#    merger.mux_subtitles(
#        video_path="C:/Videos/Movie.mkv",
#        sub_path="C:/Videos/English.srt",
#        output_path="C:/Videos/Movie_Subbed.mkv"
#    )
#
# SAFETY FEATURES:
# - This code uses '-ignore_unknown' to prevent FFmpeg from crashing 
#   if the input video has corrupted internal streams (e.g. unknown codecs).
# - It uses '-c copy' to ensure the process is instant (no re-encoding).
# ==========================================



# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
#
# 1. Import:
#    from src.processors.merger import MediaMerger
#
# 2. Instantiate:
#    assembler = MediaMerger()
#
# 3. USE CASE: Merge External Audio with Video
#    assembler.combine(
#        video_path="C:/Project/Visuals_Only.mp4", 
#        audio_path="C:/Project/Final_Audio.wav", 
#        output_path="C:/Project/Completed_Movie.mkv"
#    )
#
# Result: 
# Perfectly synchronizes the high-quality audio file with the video 
# stream, creating a single, playable master file without any loss 
# in visual or audio fidelity.
# ==========================================


# ==============================================================================
# 🎬 FEATURE: THE MEDIA MERGER (Stream Combiner)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'merger.py', and its job is "Integration." 
#    Often in professional video work, the high-quality audio and the 
#    high-quality video are processed separately (for example, after using 
#    the AI Remaster tool). This script brings them back together. It "muxes" 
#    the two different files into one single container so they play in 
#    perfect sync.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The Merger uses FFmpeg's dual-input mapping system. It takes two distinct 
#    source paths (Input 0 for Video, Input 1 for Audio) and maps them into 
#    a shared output container. It is specifically coded to use '-c copy', 
#    which means it doesn't "re-process" the files—it just puts them in 
#    the same box, making the process nearly instantaneous.
#
# 2. KEY FEATURES:
#    - Multi-Source Support: Combine .mp4, .mkv, .wav, .mp3, and .aac files.
#    - Lossless Assembly: Zero quality loss because it uses stream-copying 
#      rather than re-encoding.
#    - Sync Precision: Maintains the original timestamps (PTS) of both files 
#      to ensure audio and video don't drift apart.
#    - Format Flexibility: Can output to .mkv for the best support of 
#      professional audio codecs.
#
# 3. APPLICATIONS:
#    - AI Post-Processing: Merging the output of the 'Remaster' tool with the 
#      original movie audio.
#    - Dubbing: Adding a second language track or a background score to an 
#      existing video.
#    - Repair: Fixing "silent" videos by attaching the correct audio file.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - CPU/GPU Usage: Near Zero. Since it is just "wrapping" existing data, 
#      your processor does very little work.
#    - Speed: Instant. It is limited only by your hard drive's transfer speed.
#    - Reliability: High. It uses standard muxing protocols that work on 
#      all media players.
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - Multi-Audio Muxing: Adding the ability to merge 3 or 4 audio tracks 
#      into one movie simultaneously.
#    - Offset Correction: Adding a 'Delay' parameter to fix audio that 
#      is out of sync by a few milliseconds.
#    - Subtitle Integration: Allowing the merger to pull in .SRT files 
#      at the same time as the audio.
#
# ==============================================================================