import os
import subprocess

class ColorStudioProcessor:
    """
    Onyx Engine Color Grading & Look-Up Table (LUT) Studio
    -----------------------------------------------------
    Applies real-time color correction profiles to video streams,
    adjusting brightness, contrast, saturation, and gamma, or
    applying cinematic 3D LUTs (.cube files) losslessly preserving audio.
    """
    def adjust_colors(self, input_path: str, output_path: str, 
                      brightness: float = 0.0, 
                      contrast: float = 1.0, 
                      saturation: float = 1.0, 
                      gamma: float = 1.0, 
                      lut_path: str = None) -> bool:
                      
        if not os.path.exists(input_path):
            print(f"[ERROR] Input video does not exist: {input_path}")
            return False

        print(f"🎬 Initializing Color Studio Pipeline for: {os.path.basename(input_path)}...")
        print(f"🔧 Adjustments -> Brightness: {brightness}, Contrast: {contrast}, Saturation: {saturation}, Gamma: {gamma}")

        # Initialize the FFmpeg video filter chain array to construct a complex filter graph dynamically.
        filter_chain = []
        
        # Build the standard eq video filter
        # brightness: -1.0 to 1.0 (default 0)
        # contrast: -2.0 to 2.0 (default 1)
        # saturation: 0.0 to 3.0 (default 1)
        # gamma: 0.1 to 10.0 (default 1)
        eq_filter = f"eq=brightness={brightness}:contrast={contrast}:saturation={saturation}:gamma={gamma}"
        filter_chain.append(eq_filter)

        # Apply 3D LUT file if provided for cinematic color grading
        if lut_path and os.path.isfile(lut_path):
            print(f"🎨 Embedding 3D LUT Table: {os.path.basename(lut_path)}")
            # Escape Windows filesystem paths to conform with FFmpeg's strict syntax requirements for the lut3d filter.
            clean_lut_path = lut_path.replace("\\", "/").replace(":", "\\:")
            filter_chain.append(f"lut3d=file='{clean_lut_path}'")

        # Compile the individual filter strings into a single comma-separated video filter (vf) argument.
        vf_str = ",".join(filter_chain)

        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', vf_str,        # Pass the constructed video filter graph
            '-c:v', 'libx264',    # Enforce standard H.264 video encoding
            '-preset', 'fast',    # Balance between encoding speed and compression ratio
            '-crf', '20',         # Constant Rate Factor: 20 ensures near-transparent visual quality
            '-c:a', 'copy',       # Multiplex original audio streams untouched to preserve fidelity
            '-ignore_unknown',    # Bypass non-standard data streams (e.g., proprietary metadata) to prevent failure
            output_path
        ]

        try:
            # Execute FFmpeg process synchronously; suppress verbose output to maintain clean UI logs
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            print(f"✅ Color grading complete! Saved at: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            # Safely capture and isolate sub-process failures
            print(f"❌ Color Studio Engine failure: {str(e)}")
            return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python color_studio.py <input_video> <output_video> [brightness] [contrast] [saturation] [gamma] [lut_path]")
        sys.exit(1)
        
    studio = ColorStudioProcessor()
    b = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    c = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    s = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
    g = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
    lut = sys.argv[7] if len(sys.argv) > 7 else None
    
    studio.adjust_colors(sys.argv[1], sys.argv[2], b, c, s, g, lut)


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.color_studio import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (color_studio.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'color_studio.py', is a core component of the Onyx Engine. It is
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
