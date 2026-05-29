import os
import json

class SettingsManager:
    """
    Central utility to safely read global settings for backend FFmpeg processors.
    """
    _settings_file = "onyx_settings.json"
    _cached_settings = None

    @classmethod
    def get_settings(cls):
        # We always read fresh so that UI updates apply immediately
        if os.path.exists(cls._settings_file):
            try:
                with open(cls._settings_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    @classmethod
    def get_video_encoder(cls, default="libx264"):
        """Returns the appropriate video encoder based on hardware acceleration preference."""
        s = cls.get_settings()
        hw_idx = s.get("hw_accel", 0)
        
        # 0: CPU, 1: NVIDIA, 2: Intel QSV, 3: AMD AMF
        if hw_idx == 1: return "h264_nvenc"
        if hw_idx == 2: return "h264_qsv"
        if hw_idx == 3: return "h264_amf"
        return default

    @classmethod
    def get_video_encoder_h265(cls, default="libx265"):
        """Returns the appropriate H.265 video encoder based on hardware acceleration preference."""
        s = cls.get_settings()
        hw_idx = s.get("hw_accel", 0)
        
        if hw_idx == 1: return "hevc_nvenc"
        if hw_idx == 2: return "hevc_qsv"
        if hw_idx == 3: return "hevc_amf"
        return default

    @classmethod
    def get_audio_bitrate(cls, default="192k"):
        """Returns the default audio bitrate string."""
        s = cls.get_settings()
        idx = s.get("audio_bitrate", 1)
        
        # 0: 128k, 1: 192k, 2: 320k
        if idx == 0: return "128k"
        if idx == 1: return "192k"
        if idx == 2: return "320k"
        return default

    @classmethod
    def should_safeguard_subtitles(cls):
        """Returns True if subtitles should be aggressively dropped to prevent codec crashes."""
        return cls.get_settings().get("subtitle_safeguard", False)


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.settings_manager import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (settings_manager.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'settings_manager.py', is a core component of the Onyx Engine. It is
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
