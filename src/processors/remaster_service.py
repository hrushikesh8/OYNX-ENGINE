import os
import subprocess
from pathlib import Path

class RemasterService:
    def __init__(self, output_base="remastered_outputs"):
        self.output_base = Path(output_base)
        self.output_base.mkdir(exist_ok=True)

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

        # 1. SET THE ABSOLUTE PATH TO YOUR EXE
        ai_engine = r"C:\Users\Hrushikesh Bunni\Downloads\H\PROJECTS\VidFlow\realesrgan-ncnn-vulkan.exe"

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