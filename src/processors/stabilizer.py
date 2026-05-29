import os
import subprocess

class VideoStabilizerProcessor:
    """
    Onyx Engine Intelligent Video Stabilizer
    --------------------------------------
    Uses FFmpeg's two-pass vid.stab filters to analyze video frame motions (Pass 1)
    and smooth out camera shakiness (Pass 2) without losing audio quality.
    """
    def stabilize(self, input_path: str, output_path: str, 
                  shakiness: int = 10, 
                  accuracy: int = 15, 
                  smoothing: int = 30) -> bool:
                  
        if not os.path.exists(input_path):
            print(f"[ERROR] Input video does not exist: {input_path}")
            return False

        base_dir = os.path.dirname(output_path)
        trf_file = os.path.join(base_dir, "transforms.trf")
        
        print(f"🎬 Initializing 2-Pass Video Stabilization for: {os.path.basename(input_path)}")
        
        # Pass 1: Motion Vector Analysis
        # Utilizes the vidstabdetect filter to compute affine transformations between adjacent frames.
        # Data is serialized into a .trf coordinate matrix file rather than modifying the video.
        print("🔍 Pass 1/2: Analyzing camera movement vectors...")
        pass1_cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', f"vidstabdetect=shakiness={shakiness}:accuracy={accuracy}:result='{trf_file.replace(os.sep, '/')}'",
            '-f', 'null', '-'
        ]
        
        try:
            subprocess.run(pass1_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(f"❌ Pass 1 analysis failed: {str(e)}")
            if os.path.exists(trf_file):
                try: os.remove(trf_file)
                except Exception: pass
            return False

        # Pass 2: Matrix Transformation & Frame Synthesis
        # Executes vidstabtransform by reading the .trf matrix.
        # Applies a Low-Pass Filter (smoothing factor) and bilinear interpolation to eliminate micro-jitter.
        print("🎥 Pass 2/2: Synthesizing stabilized video frames...")
        pass2_cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', f"vidstabtransform=input='{trf_file.replace(os.sep, '/')}':smoothing={smoothing}:interpol=bilinear",
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '20',
            '-c:a', 'copy',       # Bypasses the audio encoder to ensure absolute phase lock.
            '-ignore_unknown',
            output_path
        ]
        
        try:
            subprocess.run(pass2_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            print(f"✅ Stabilization complete! Saved output at: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Pass 2 smoothing failed: {str(e)}")
            return False
        finally:
            # Clean up the temporary transforms.trf file
            if os.path.exists(trf_file):
                try:
                    os.remove(trf_file)
                except Exception:
                    pass

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python stabilizer.py <input_video> <output_video> [shakiness] [accuracy] [smoothing]")
        sys.exit(1)
        
    stabilizer = VideoStabilizerProcessor()
    shakiness_val = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    accuracy_val = int(sys.argv[4]) if len(sys.argv) > 4 else 15
    smoothing_val = int(sys.argv[5]) if len(sys.argv) > 5 else 30
    
    stabilizer.stabilize(sys.argv[1], sys.argv[2], shakiness_val, accuracy_val, smoothing_val)


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.stabilizer import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (stabilizer.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'stabilizer.py', is a core component of the Onyx Engine. It is
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
