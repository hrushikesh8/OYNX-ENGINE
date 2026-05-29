import os
import subprocess
import re

class AudioTranscriber:
    """
    VidFlow AI Speech-to-Text Transcriber
    -----------------------------------
    Extracts the audio track from a video file, transcribes it using 
    OpenAI Whisper (if installed) or provides a clean fallback, 
    and outputs a standard synced .srt subtitle file.
    """
    def format_srt_timestamp(self, seconds: float) -> str:
        """Converts seconds into SRT format HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds % 1) * 1000))
        if millis >= 1000:
            millis = 0
            secs += 1
            if secs >= 60:
                secs = 0
                minutes += 1
                if minutes >= 60:
                    minutes = 0
                    hours += 1
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def transcribe(self, input_video: str, output_srt: str, language: str = None, model_name: str = "tiny") -> bool:
        if not os.path.exists(input_video):
            print(f"[ERROR] Input video does not exist: {input_video}")
            return False

        # Generate a temporary 16kHz mono WAV file for clean speech recognition
        temp_audio = os.path.join(os.path.dirname(input_video), "temp_extract_voice.wav")
        print(f"🔊 Extracting voice track to: {temp_audio}...")
        
        extract_cmd = [
            'ffmpeg', '-y',
            '-i', input_video,
            '-vn',                # No video
            '-acodec', 'pcm_s16le', # Uncompressed PCM WAV
            '-ar', '16000',       # 16kHz sample rate (optimal for speech tools)
            '-ac', '1',           # Mono channel
            temp_audio
        ]
        
        try:
            subprocess.run(extract_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except Exception as e:
            print(f"[ERROR] Audio extraction failed: {str(e)}")
            return False

        try:
            # Attempt to use OpenAI Whisper library
            import whisper
            print(f"🧠 Loading Whisper AI model ({model_name}). Please wait...")
            model = whisper.load_model(model_name)
            
            print("🎙️ Running Speech-to-Text Transcription...")
            options = {}
            if language:
                options["language"] = language
                
            result = model.transcribe(temp_audio, **options)
            
            print(f"📝 Writing subtitles to SRT: {output_srt}...")
            with open(output_srt, "w", encoding="utf-8") as f:
                for idx, segment in enumerate(result.get("segments", []), 1):
                    start_str = self.format_srt_timestamp(segment["start"])
                    end_str = self.format_srt_timestamp(segment["end"])
                    text = segment["text"].strip()
                    
                    f.write(f"{idx}\n")
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{text}\n\n")
            
            print("🎉 Transcription complete!")
            return True
            
        except ImportError:
            print("\n⚠️ [Whisper Missing] OpenAI Whisper package is not installed.")
            print("💡 Running in offline mock/fallback mode.")
            print("💡 To enable state-of-the-art AI speech-to-text, run: pip install openai-whisper")
            
            # Simple mock subtitle generator based on voice energy detection, or dummy dialogue for demo
            print(f"📝 Generating fallback dialogue subtitles to SRT: {output_srt}...")
            with open(output_srt, "w", encoding="utf-8") as f:
                dialogues = [
                    (0.0, 5.0, "[Music Intro] Welcome to Onyx Engine v3.0 Production Suite."),
                    (5.5, 12.0, "This is an automated placeholder subtitle. Install the Whisper package for AI speech-to-text transcription."),
                    (13.0, 20.0, "Onyx allows you to remaster footage, clean audio, merge formats, and compile editing timelines.")
                ]
                for idx, (start, end, text) in enumerate(dialogues, 1):
                    start_str = self.format_srt_timestamp(start)
                    end_str = self.format_srt_timestamp(end)
                    f.write(f"{idx}\n")
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{text}\n\n")
            return True
            
        finally:
            # Clean up temporary audio file
            if os.path.exists(temp_audio):
                try:
                    os.remove(temp_audio)
                except Exception:
                    pass

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python transcription.py <video_path> <output_srt>")
        sys.exit(1)
    transcriber = AudioTranscriber()
    transcriber.transcribe(sys.argv[1], sys.argv[2])


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.transcription import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (transcription.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'transcription.py', is a core component of the Onyx Engine. It is
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
