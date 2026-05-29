import subprocess
import json
import os
import glob
from pathlib import Path
from src.processors.settings_manager import SettingsManager

class MetadataEditor:
    """
    VidFlow Container Metadata Tag Editor
    --------------------------------------
    Uses ffprobe to extract global container tags (Title, Artist, Genre, etc.)
    and FFmpeg stream copy to write updated tags instantly.
    """
    def read_metadata(self, input_path: str) -> dict:
        """Reads global metadata tags from a video file."""
        if not os.path.exists(input_path):
            return {}

        # Construct the FFprobe command to dump container formatting data purely as a JSON object
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format',
            '-of', 'json',
            input_path
        ]
        try:
            # Execute FFprobe and capture the standard output securely for parsing
            output = subprocess.check_output(cmd)
            data = json.loads(output)
            # Safely navigate the JSON tree to return existing container tags, defaulting to an empty dict
            return data.get('format', {}).get('tags', {})
        except Exception as e:
            # Isolate FFprobe read failures without bubbling the exception to the UI
            print(f"❌ Error reading metadata tags: {e}")
            return {}

    def write_metadata(self, input_path: str, output_path: str, tags: dict) -> list:
        """
        Generates the FFmpeg command list to write metadata tags.
        Returns the command list to be executed by the TaskWorker.
        """
        # Map 0 (all streams) and copy codecs (lossless, instant)
        # Conditional stream mapping to intelligently safeguard MKV subtitle tracks based on user settings
        maps = ['-map', '0:v', '-map', '0:a?'] if SettingsManager.should_safeguard_subtitles() else ['-map', '0']
        
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
        ] + maps + [
            '-c', 'copy',          # Engage stream-copy mode to avoid re-encoding latency and quality degradation
            '-ignore_unknown'      # Mitigate crashes caused by unsupported stream types in obscure container formats
        ]

        # Iteratively append standard metadata injection flags for each key-value pair provided
        for key, val in tags.items():
            cmd.extend(['-metadata', f'{key}={val}'])

        # Finalize the command array with the designated output path
        cmd.append(output_path)
        return cmd


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.metadata_editor import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (metadata_editor.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'metadata_editor.py', is a core component of the Onyx Engine. It is
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
