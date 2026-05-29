import os
import subprocess
from pathlib import Path

class RemasterService:
    def __init__(self, output_base="remastered_outputs", ai_engine_path=None):
        self.output_base = Path(output_base)
        self.output_base.mkdir(exist_ok=True)
        self.ai_engine = ai_engine_path or "realesrgan-ncnn-vulkan.exe"

    def _run_cmd(self, cmd):
        """Standard runner for VidFlow sub-processes."""
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] VidFlow Remaster Engine failed: {e}")

    def generate_sample(self, input_path):
        """
        Feature 14.1: The Extractor.
        Grabs 2 minutes from the 5-minute mark for quality check.
        """
        input_path = Path(input_path)
        sample_raw = "temp_raw_slice.mp4"
        sample_final = self.output_base / f"SAMPLE_{input_path.name}"

        # Extracting the 2-minute slice
        self._run_cmd([
            "ffmpeg", "-y", "-ss", "00:05:00", "-t", "00:02:00",
            "-i", str(input_path), "-c", "copy", sample_raw
        ])

        # Process only the slice
        self._process_pipeline(sample_raw, str(sample_final))
        
        if os.path.exists(sample_raw): os.remove(sample_raw)
        return sample_final

    def start_full_remaster(self, input_path):
        """
        Feature 14.2: The Full Restoration.
        Automated 12-18 hour process.
        """
        input_path = Path(input_path)
        final_out = self.output_base / f"REMASTERED_{input_path.name}"
        
        self._process_pipeline(str(input_path), str(final_out))
        return final_out

    def _process_pipeline(self, in_file, out_file):
        """The Core AI Restoration and Encoding Pipeline."""
        temp_upscale = "temp_upscaling_buffer.mp4"

        # Dynamic AI engine executable from settings
        ai_engine = self.ai_engine

        # Step A: AI Upscaling (Utilizing RTX GPU)
        self._run_cmd([
            ai_engine, "-i", in_file, "-o", temp_upscale,
            "-s", "2", "-n", "realesr-general-x4v3"
        ])

        # Step B: Cinematic Polish & H.265 (HEVC) Encoding
        # -crf 22: High quality, 30-50% size increase
        # noise=alls=3: Adds the 'Godfather' theatrical film grain
        self._run_cmd([
            "ffmpeg", "-y", "-i", temp_upscale,
            "-vf", "eq=saturation=1.1:contrast=1.03, noise=alls=3:allf=t",
            "-c:v", "libx265", "-crf", "22", "-preset", "slow",
            "-c:a", "copy", # Preserving original movie audio mix
            out_file
        ])

        # Cleanup intermediate buffer
        if os.path.exists(temp_upscale):
            os.remove(temp_upscale)

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.remaster_service import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (remaster_service.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'remaster_service.py', is a core component of the Onyx Engine. It is
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
