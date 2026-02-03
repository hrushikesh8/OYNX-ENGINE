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