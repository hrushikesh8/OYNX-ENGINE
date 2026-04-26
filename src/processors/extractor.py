import subprocess
import os
import sys
import glob
from pathlib import Path

class AudioExtractor:
    def extract_audio(self, input_path: str, output_format: str = "mp3", track_id: int = 0):
        """
        Extracts a specific audio track from a video.
        output_format: 'mp3', 'wav', 'aac', or 'original' (copy stream).
        track_id: Defaults to 0 (the first/main audio track).
        """
        # --- FILENAME & PATH LOGIC (ORIGINAL PRESERVATION) ---
        filename = Path(input_path).stem
        output_folder = os.path.dirname(input_path)
        
        # Determine output extension
        ext = output_format if output_format != "original" else "aac"
        
        # We append the track_id to the filename if it's not the main track
        # so you don't accidentally overwrite files when ripping multiple languages.
        suffix = f"_Track{track_id}" if track_id > 0 else ""
        output_path = os.path.join(output_folder, f"{filename}{suffix}.{ext}")

        # --- THE COMMAND (UPGRADED) ---
        # Instead of just '-vn' (which blindly grabs default audio), we use '-map 0:a:X'.
        # This surgically targets the exact audio channel you want.
        command = [
            'ffmpeg', '-i', input_path, 
            '-map', f'0:a:{track_id}', 
            '-avoid_negative_ts', 'make_zero' # 🚀 SEAMLESS SERVER UPGRADE
        ]

        if output_format == "original":
            # Stream Copy (Instant, no quality loss)
            command.extend(['-c:a', 'copy'])
        elif output_format == "mp3":
            # High Quality MP3 (VBR Setting 2 - Perfect for Music)
            command.extend(['-c:a', 'libmp3lame', '-q:a', '2'])
        elif output_format == "wav":
            # Uncompressed Audio
            command.extend(['-c:a', 'pcm_s16le'])
        else:
            # Generic re-encode for other formats
            command.extend(['-c:a', 'aac'])

        command.extend(['-y', output_path])

        try:
            print(f"🎵 VidFlow Extractor: Ripping Track {track_id} as {output_format.upper()}...")
            subprocess.run(command, check=True, capture_output=True)
            return True, output_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Error on {filename}: {e.stderr.decode()}")
            return False, None

    def extract_folder(self, folder_path: str, output_format: str = "mp3", track_id: int = 0):
        """
        🚀 NEW FEATURE: The Mass Harvester.
        Scans a folder and rips the audio from every video inside it.
        """
        print(f"📂 VidFlow Batch: Scanning '{os.path.basename(folder_path)}' for videos...")
        
        # Search for common video formats recursively
        search_patterns = ['*.mp4', '*.mkv', '*.avi', '*.mov', '*.webm']
        tasks = []
        for ext in search_patterns:
            tasks.extend(glob.glob(os.path.join(folder_path, '**', ext), recursive=True))

        if not tasks:
            print("❌ No videos found in the specified folder.")
            return False

        print(f"🚀 Found {len(tasks)} videos. Starting Mass Extraction...\n" + "-"*40)
        
        success_count = 0
        for vid in tasks:
            success, _ = self.extract_audio(vid, output_format, track_id)
            if success:
                success_count += 1
                
        print("-" * 40)
        print(f"🎉 Batch Complete! Ripped {success_count}/{len(tasks)} files to {output_format.upper()}.")
        return success_count > 0

# --- STANDALONE EXECUTION LOGIC (UPGRADED FOR FOLDERS) ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ VidFlow Error: Missing arguments.")
        print("Usage: python extractor.py <file_or_folder_path> [format:mp3|wav|original] [track_id:0,1,2...]")
        sys.exit(1)

    target_path = sys.argv[1]
    fmt = sys.argv[2] if len(sys.argv) > 2 else "mp3"
    tid = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    
    extractor = AudioExtractor()
    
    # Logic: Auto-detect if user gave a Folder or a single File
    if os.path.isdir(target_path):
        extractor.extract_folder(target_path, fmt, tid)
    elif os.path.isfile(target_path):
        success, out = extractor.extract_audio(target_path, fmt, tid)
        if success:
            print(f"✅ Extracted: {out}")
    else:
        print("❌ Invalid path provided.")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLES)
# ==========================================
#
# Option 1: Rip a Single Music Video to High-Quality MP3
# python src/processors/extractor.py "C:/Downloads/Concert.mp4" "mp3"
#
# Option 2: The Mass Harvester (Rip a whole folder of music videos at once)
# python src/processors/extractor.py "C:/Downloads/Music_Videos_Folder" "mp3"
#
# Option 3: Extract a Specific Movie Language (e.g., Track 2 = Telugu)
# python src/processors/extractor.py "C:/Movies/Epic_Movie.mkv" "original" "1"
#
# Result: 
# Flawless audio extraction. If you point it at a folder with 50 music 
# videos, it will automatically rip all 50 to your preferred format 
# without you needing to type 50 commands.
# ==========================================


# ==============================================================================
# 🎬 FEATURE: THE AUDIO HARVESTER (AudioExtractor)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'extractor.py'. It is a surgical "Aural Isolation" tool. 
#    It allows you to strip the audio away from the visuals. This is the ultimate 
#    tool for building a music library—you can download 100 music videos, 
#    point this tool at the folder, and it will give you 100 perfectly 
#    formatted MP3s.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The Extractor utilizes FFmpeg's stream mapping (`-map 0:a:X`). Instead of 
#    just dropping the video, it specifically targets the exact audio channel 
#    you want. It supports both single-file processing and recursive directory 
#    scanning (The Harvester mode).
#
# 2. KEY FEATURES:
#    - Multi-Track Scoped Upgrade: Allows the user to select Track 0 (Main), 
#      Track 1 (Dubbed), Track 2 (Commentary), etc.
#    - Batch Harvester Upgrade: Automatically finds and processes all videos 
#      inside a folder and its sub-folders.
#    - High-Fidelity MP3: Uses the 'libmp3lame' encoder with Variable Bitrate 
#      (-q:a 2) to ensure music sounds studio-quality.
#    - Lossless Mode: 'original' format uses stream copying for instant execution.
#
# 3. APPLICATIONS:
#    - Music Library Creation: Turning a folder of YouTube rips into MP3s.
#    - Multi-Language Ripping: Pulling the Hindi or Telugu dub out of a 
#      Hollywood MKV file.
#
# ==============================================================================