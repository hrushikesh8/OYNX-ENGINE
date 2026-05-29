import subprocess
import re
import os

class SilenceRemover:
    """
    VidFlow Lossless Silence Remover (Auto-Trim)
    -------------------------------------------
    Uses FFmpeg silencedetect filter to find audio silence below a threshold,
    and then maps the non-silent intervals into an instant concat demuxer list
    to trim silent sections without re-encoding.
    """
    def remove_silence(self, input_path: str, output_path: str, noise_db: int = -35, min_silence_len: float = 0.5) -> bool:
        if not os.path.exists(input_path):
            print("❌ Input path does not exist.")
            return False

        print(f"⚡ Detecting silent segments (Threshold: {noise_db}dB, Min Len: {min_silence_len}s)...")
        # Step 1: Perform a high-speed audio-only analysis pass utilizing the internal 'silencedetect' graph filter.
        # Outputting to the 'null' muxer prevents writing a dummy file to disk during the analytical phase.
        cmd = [
            'ffmpeg', '-i', input_path,
            '-af', f'silencedetect=noise={noise_db}dB:duration={min_silence_len}',
            '-f', 'null', '-'
        ]
        try:
            # We run the command and parse stderr for silence_start and silence_end logs
            process = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
            output = process.stderr
            
            starts = [float(x) for x in re.findall(r'silence_start:\s*([\d\.]+)', output)]
            ends = [float(x) for x in re.findall(r'silence_end:\s*([\d\.]+)', output)]
            
            # Find total duration of video
            duration_match = re.search(r'Duration:\s*([\d\:]+)', output)
            total_duration = 0.0
            if duration_match:
                time_str = duration_match.group(1)
                h, m, s = time_str.split(':')
                total_duration = int(h)*3600 + int(m)*60 + float(s)

            if not starts or len(starts) != len(ends):
                if len(starts) > len(ends):
                    ends.append(total_duration)
                else:
                    print("⚠️ No silence detected or parsing mismatch. Outputting copy.")
                    # Fallback copy
                    subprocess.run(['ffmpeg', '-y', '-i', input_path, '-c', 'copy', output_path])
                    return True

            # Step 2: Compute non-silent (active) intervals
            active_intervals = []
            current_start = 0.0
            for s_start, s_end in zip(starts, ends):
                if s_start > current_start + 0.1: # Save segments longer than 0.1s
                    active_intervals.append((current_start, s_start))
                current_start = s_end
            if current_start < total_duration - 0.1:
                active_intervals.append((current_start, total_duration))

            if not active_intervals:
                print("❌ The entire video is detected as silence. Aborting.")
                return False

            print(f"🎬 Found {len(active_intervals)} active segments. Stitching losslessly...")

            # Step 3: Write temporary concat file using absolute path
            list_file = os.path.join(os.path.dirname(output_path), "silence_concat.txt")
            with open(list_file, "w", encoding="utf-8") as f:
                for start, end in active_intervals:
                    # Concat demuxer syntax with inpoint/outpoint seeking
                    f.write(f"file '{input_path.replace(os.sep, '/')}'\n")
                    f.write(f"inpoint {start}\n")
                    f.write(f"outpoint {end}\n")

            # Step 4: Execute the FFmpeg concat demuxer process synchronously.
            # -f concat allows us to stitch multiple in/out segments of the same file sequentially
            # while maintaining the -c copy strictness (Zero re-encoding logic).
            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat', '-safe', '0',
                '-i', list_file,
                '-c', 'copy',
                '-ignore_unknown',
                output_path
            ]
            
            subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            
            # Cleanup
            if os.path.exists(list_file):
                os.remove(list_file)
            
            print(f"🎉 Lossless Silence Removal complete! Saved to: {output_path}")
            return True

        except Exception as e:
            print(f"❌ Error during silence removal: {str(e)}")
            if 'list_file' in locals() and os.path.exists(list_file):
                os.remove(list_file)
            return False


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.silence_remover import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (silence_remover.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'silence_remover.py', is a core component of the Onyx Engine. It is
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
