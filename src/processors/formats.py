import os
import subprocess
from pathlib import Path
import glob
from src.processors.settings_manager import SettingsManager
from src.processors.time_machine import TimeMachine

class FormatMapper:
    """
    🎬 FEATURE: THE VIDEO FORMAT CONVERTER (Original Logic Intact)
    """
    # Define codec rules for different containers to ensure compatibility
    FORMAT_RULES = {
        'mkv': ['-c:v', 'copy', '-c:a', 'copy', '-c:s', 'srt'],  # Lossless video/audio, safe SRT subs
        'mp4': ['-c:v', 'copy', '-c:a', 'aac', '-c:s', 'mov_text'], # Best for compatibility
        'avi': ['-c:v', 'copy', '-c:a', 'copy'],
        'mov': ['-c:v', 'copy', '-c:a', 'aac', '-c:s', 'mov_text'],
        'flv': ['-c:v', 'flv', '-c:a', 'aac'],
        'webm': ['-c:v', 'libvpx-vp9', '-c:a', 'libopus'],  # WebM usually needs re-encoding
        'mpg': ['-c:v', 'mpeg2video', '-c:a', 'mp2'],       # MPG requires specific MPEG codecs
        'mpeg': ['-c:v', 'mpeg2video', '-c:a', 'mp2'],      # Same as MPG
    }

    def convert_video(self, input_path: str, output_folder: str, target_format: str, run_id: str | None = None) -> dict:
        """Helper function to convert a single file using a resilient 5-Tier Ultra-Fast Strategy."""
        filename = Path(input_path).stem
        output_path = os.path.join(output_folder, f"{filename}.{target_format}")
        
        encoder = SettingsManager.get_video_encoder()
        audio_bitrate = SettingsManager.get_audio_bitrate()

        # Decide stream mapping based on Subtitle Safeguard setting
        if SettingsManager.should_safeguard_subtitles():
            tier_map = ['-map', '0:v:0', '-map', '0:a?']
        else:
            tier_map = ['-map', '0:v:0', '-map', '0:a?', '-map', '0:s?']

        # Tier 1: Pure Stream Copy with Timestamp Normalization (Instant ~2s, clean index for VLC seeking)
        cmd_tier1 = ['ffmpeg', '-fflags', '+genpts', '-i', input_path, *tier_map, '-c:v', 'copy', '-c:a', 'copy', '-avoid_negative_ts', 'make_zero', '-ignore_unknown', '-y', output_path]
        
        # Tier 2: Video Stream Copy + AAC Audio Transcode (Video copied, audio to AAC ~5s, clean index)
        cmd_tier2 = ['ffmpeg', '-fflags', '+genpts', '-i', input_path, '-map', '0:v:0', '-map', '0:a?', '-c:v', 'copy', '-c:a', 'aac', '-b:a', audio_bitrate, '-avoid_negative_ts', 'make_zero', '-ignore_unknown', '-y', output_path]
        
        # Tier 3: GPU Hardware-Accelerated Transcode (NVENC / QSV / AMF / MF)
        if encoder and encoder != "libx264":
            cmd_tier3 = ['ffmpeg', '-i', input_path, '-map', '0:v:0', '-map', '0:a?', '-c:v', encoder, '-c:a', 'aac', '-b:a', audio_bitrate, '-ignore_unknown', '-y', output_path]
        else:
            cmd_tier3 = ['ffmpeg', '-i', input_path, '-map', '0:v:0', '-map', '0:a?', '-c:v', 'libx264', '-preset', 'superfast', '-crf', '22', '-c:a', 'aac', '-b:a', audio_bitrate, '-ignore_unknown', '-y', output_path]

        # Tier 4: High-Speed CPU Software Transcode (Superfast preset)
        cmd_tier4 = ['ffmpeg', '-i', input_path, '-map', '0:v:0', '-map', '0:a?', '-c:v', 'libx264', '-preset', 'superfast', '-crf', '22', '-c:a', 'aac', '-b:a', audio_bitrate, '-ignore_unknown', '-y', output_path]

        # Tier 5: Universal Emergency Fallback (Ultrafast preset)
        cmd_tier5 = ['ffmpeg', '-i', input_path, '-map', '0:v:0', '-map', '0:a?', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '24', '-c:a', 'aac', '-b:a', audio_bitrate, '-ignore_unknown', '-y', output_path]

        print(f"    [Convert] {filename} -> .{target_format}")
        
        attempts = [
            ("Tier 1 (Instant Pure Stream Copy)", cmd_tier1),
            ("Tier 2 (Video Stream Copy + AAC Audio)", cmd_tier2),
            (f"Tier 3 (GPU Hardware Transcode - {encoder})", cmd_tier3),
            ("Tier 4 (High-Speed CPU Superfast)", cmd_tier4),
            ("Tier 5 (Universal Emergency Ultrafast)", cmd_tier5)
        ]
        
        last_error = ""
        for tier_name, cmd in attempts:
            try:
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE

                subprocess.run(cmd, check=True, capture_output=True, startupinfo=startupinfo)
                if run_id:
                    TimeMachine.log_action("Format Converter", run_id, f"CONVERT_{target_format.upper()}", input_path, output_path, op_type="CREATE")
                return {"status": "success", "file": filename}
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
                last_error = err_msg.strip().split('\n')[-1] if err_msg else str(e)
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except Exception:
                        pass

        return {"status": "error", "file": filename, "message": last_error}

    def process_input(self, input_path: str, output_folder: str, target_format: str, run_id: str | None = None):
        """
        Smart Processor: Handles both Single Files and Folders (Batch).
        """
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        tasks = []
        
        if os.path.isdir(input_path):
            print(f"Scanning folder for videos...")
            extensions = (
                '*.mp4', '*.mkv', '*.avi', '*.mov', '*.flv', '*.wmv', 
                '*.mpg', '*.mpeg', '*.webm', '*.m4v', '*.ts', '*.vob', '*.3gp'
            )
            for ext in extensions:
                tasks.extend(glob.glob(os.path.join(input_path, ext), recursive=False))
        
        elif os.path.isfile(input_path):
            tasks = [input_path]
        
        else:
            print("[Error] Invalid input path.")
            return 0, 0

        if not tasks:
            print("[Error] No video files found.")
            return 0, 0

        print(f"[Info] Processing {len(tasks)} files...")
        print("-" * 40)

        success_count = 0
        error_count = 0

        for file_path in tasks:
            # Skip if already in target format
            if file_path.lower().endswith(f".{target_format}"):
                print(f"    [Skip] {os.path.basename(file_path)} (already matches format)")
                continue

            result = self.convert_video(file_path, output_folder, target_format, run_id)
            
            if result['status'] == 'success':
                print(f"    [Done] {result['file']}")
                success_count += 1
            else:
                print(f"    [Failed] {result['file']}")
                error_count += 1

        print("-" * 40)
        print(f"[Complete] Success: {success_count} | Errors: {error_count}")
        return success_count, error_count

# --- YOUR ORIGINAL DOCUMENTATION PRESERVED AT BOTTOM ---
# ==========================================
# HOW TO USE THIS CODE (DOCUMENTATION)
# ==========================================
#
# 1. Import:
#    from src.processors.formats import FormatMapper
#
# 2. Instantiate:
#    converter = FormatMapper()
#
# 3. USE CASE A: Batch Convert a Folder
#    converter.process_input(
#        input_path="C:/Downloads/Movies/", 
#        output_folder="C:/Downloads/Movies/Converted", 
#        target_format="mp4"
#    )
#
# 4. USE CASE B: Convert Single File
#    converter.process_input(
#        input_path="C:/Video.mkv", 
#        output_folder="C:/Converted", 
#        target_format="avi"
#    )
# ==========================================






# ==============================================================================
# 🎬 FEATURE: THE VIDEO FORMAT CONVERTER
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'formats.py', and its job is "Transformation." 
#    It takes a video in one format (like an old .AVI or .MKV) and changes it 
#    into a modern format (like .MP4). This is the most basic yet essential 
#    part of the engine, ensuring that any file you have can be played on 
#    your phone, TV, or server without compatibility errors.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The Formats Engine uses FFmpeg to re-wrap or re-encode video streams. 
#    It handles 'Transcoding' (changing the codec) and 'Transmuxing' 
#    (changing the container). It is designed to be a loss-less or high-bitrate 
#    bridge between different media standards.
#
# 2. KEY FEATURES:
#    - Multi-Container Support: Handles .mp4, .mkv, .mov, .avi, and .flv.
#    - Codec Optimization: Primarily uses H.264 for maximum compatibility.
#    - Stream Mapping: Automatically identifies and carries over the best 
#      available video and audio streams from the source.
#    - Fast-Transmuxing: Skips encoding if the source and target are compatible.
#
# 3. APPLICATIONS:
#    - Library Standardization: Converting a messy folder of different file 
#      types into a uniform MP4 library for a server.
#    - Device Compatibility: Fixing videos that "won't open" on specific 
#      players by converting them to standard formats.
#    - Editing Prep: Converting high-compression files into formats that 
#      are easier for editing software to handle.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - CPU/GPU Usage: Variable. If "copying" data, it is instant and uses 0% 
#      resources. If "converting," it uses a steady amount of CPU/GPU.
#    - Disk I/O: Moderate. It reads the old file and writes the new one 
#      simultaneously.
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - Batch Conversion: Implementing a "Folder-to-MP4" sweep.
#    - Preset Profiles: Adding specific "Apple TV", "Android", or "PlayStation" 
#      export settings.
#    - Hardware Auto-Detect: Automatically switching between NVENC (Nvidia) 
#      and QuickSync (Intel) for the fastest possible conversion.
#
# 6. HOW TO USE THIS MODULE:
#    Syntax:  python src/processors/formats.py <InputPath> <TargetExtension>
#    Example: python src/processors/formats.py "Holiday_Video.avi" "mp4"
#    Output:  A perfectly compatible MP4 version of your original video.
#
# ==============================================================================#

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.formats import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (formats.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'formats.py', is a core component of the Onyx Engine. It is
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
