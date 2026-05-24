import subprocess
import os
import sys

class MotionFluidizer:
    """
    VidFlow Motion Engineering Engine
    ---------------------------------
    Uses RIFE (Real-Time Intermediate Flow Estimation) AI to synthesize 
    new frames between existing ones. Increases framerate (FPS) for 
    ultra-smooth theatrical motion.
    """

    def __init__(self, bin_folder="bin"):
        """
        Initializes the path to the AI interpolation binaries.
        Can accept the absolute executable path directly, or a folder.
        """
        if bin_folder.lower().endswith(".exe"):
            self.ai_bin = bin_folder
        else:
            self.ai_bin = os.path.join(bin_folder, "rife-ncnn-vulkan.exe")

    def smooth_motion(self, input_path: str, output_path: str, multiplier: int = 2):
        """
        Executes the AI Frame Interpolation chain:
        1. Motion Analysis: Calculates the trajectory of objects between two frames.
        2. Frame Synthesis: Creates a 'perfect' middle frame.
        3. Vulkan Processing: Offloads the heavy math to the GPU for speed.

        Args:
            input_path (str): Path to the source video.
            output_path (str): Path where the high-fps video will be saved.
            multiplier (int): Speed factor (2x turns 30fps to 60fps).
        """
        
        # Security Check: Ensure the AI binary exists
        if not os.path.exists(self.ai_bin):
            print(f"❌ Critical Error: RIFE Engine not found at {self.ai_bin}")
            print("Ensure the RIFE-NCNN-Vulkan binaries are present in your /bin folder.")
            return False

        # CLI Parameters for the RIFE Engine:
        # -m: Multiplier (2, 4, 8x)
        # -g: GPU ID (Defaults to 0)
        command = [
            self.ai_bin,
            "-i", input_path,
            "-o", output_path,
            "-m", str(multiplier)
        ]

        try:
            print(f"✨ VidFlow Motion Service: Initializing AI Interpolation...")
            print(f"🚀 Processing: {os.path.basename(input_path)} -> Smoothing to {multiplier}x FPS")
            print("💎 Generating intermediate frames. GPU hardware acceleration active.")
            
            # Subprocess execution allows the user to see progress in the terminal
            subprocess.run(command, check=True)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Motion Interpolation Failed: {e}")
            return False
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            return False

# --- STANDALONE EXECUTION LOGIC ---
if __name__ == "__main__":
    # Check for file path argument
    if len(sys.argv) < 2:
        print("Usage: python motion.py <video_path>")
        sys.exit(1)

    input_file = sys.argv[1]
    
    # Generate output name automatically (e.g., movie_60FPS.mp4)
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}_60FPS.mp4"
    
    # Initialize engine
    engine = MotionFluidizer()
    
    # Run standalone test
    if engine.smooth_motion(input_file, output_file):
        print("-" * 50)
        print(f"✅ SUCCESS: {output_file} is now fluid and smooth.")
        print("-" * 50)
    else:
        print("❌ Motion smoothing aborted.")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
#
# Syntax: python src/processors/motion.py <VideoPath>
#
# Example:
# python src/processors/motion.py "C:/Movies/Old_Cinema_24fps.mp4"
#
# Result: 
# Using AI, it creates a new version of the movie that runs at 
# 48fps or 60fps, giving it a modern, high-refresh-rate "soap opera" 
# fluidity that looks incredible on 2026 displays.




# ==============================================================================
# 🎬 FEATURE: THE AI MOTION FLUIDIZER (60 FPS)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'motion.py', and its job is "Smoothness." 
#    Movies are usually filmed at 24 frames per second, which can look "choppy" 
#    on modern screens. This AI "watches" the movement in the video and 
#    creates brand-new frames to fill in the gaps. It turns a jittery movie 
#    into a buttery-smooth 60fps experience that looks amazing on new TVs.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The Motion Engine uses the RIFE (Real-Time Intermediate Flow Estimation) 
#    algorithm. It calculates the 'motion vector' of every pixel. If a ball is 
#    moving across the screen, the AI predicts where that ball would be 
#    between two frames and draws it there, doubling or tripling the framerate.
#
# 2. KEY FEATURES:
#    - Multiplier Logic: 2x (60fps) or 4x (120fps) smoothness options.
#    - Vulcan Optimized: Works on Nvidia, AMD, and Intel GPUs.
#    - Judder Elimination: Removes the stuttering look from cinematic shots.
#
# 3. APPLICATIONS:
#    - High-End Streaming: Modernizing 90s action films for a premium feel.
#    - Slow-Motion: Turning 60fps footage into silky-smooth super slow-mo.
#    - Content Remastering: Enhancing low-framerate digital recordings.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - GPU Usage: Very High. Like the Remaster tool, this is an AI-heavy task.
#    - Time Efficiency: Moderate. Faster than remastering, but still a process 
#      that benefits from being scheduled to run in the background.
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - Scene Cut Protection: Ensuring the AI doesn't warp images during cuts.
#    - Refresh Rate Sync: Automatically matching the video to the monitor's FPS.
#
# 6. HOW TO USE THIS MODULE:
#    Syntax:  python src/processors/motion.py <VideoPath>
#    Example: python src/processors/motion.py "Jittery_Movie_24fps.mp4"
#    Output:  A 60fps or high-framerate MP4 with ultra-fluid movement.
#
# ==============================================================================