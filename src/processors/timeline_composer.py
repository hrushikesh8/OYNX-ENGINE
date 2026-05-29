import os
import subprocess
import tempfile
import json
from pathlib import Path
from src.processors.settings_manager import SettingsManager

# Helper properties probe using ffprobe
def get_media_properties(file_path: str):
    """Returns (duration, width, height) using ffprobe JSON parsing."""
    try:
        cmd = [
            'ffprobe', '-v', 'error', 
            '-show_entries', 'format=duration:stream=width,height', 
            '-of', 'json', 
            file_path
        ]
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo, check=True)
        data = json.loads(result.stdout)
        
        # Parse duration
        dur = float(data.get('format', {}).get('duration', 10.0))
        
        # Find video stream width/height
        width = 1920
        height = 1080
        for stream in data.get('streams', []):
            if 'width' in stream and 'height' in stream:
                width = int(stream['width'])
                height = int(stream['height'])
                break
        return dur, width, height
    except Exception:
        return 10.0, 1920, 1080

def get_center_crop_filter(w, h, aspect):
    if not aspect or aspect == 'None':
        return ""
    try:
        if aspect == '1:1':
            size = min(w, h)
            x = (w - size) // 2
            y = (h - size) // 2
            return f"crop={size}:{size}:{x}:{y}"
        elif aspect == '9:16':
            target_ratio = 9.0 / 16.0
            current_ratio = w / h
            if current_ratio > target_ratio:
                ch = h
                cw = int(h * target_ratio)
            else:
                cw = w
                ch = int(w / target_ratio)
            x = (w - cw) // 2
            y = (h - ch) // 2
            return f"crop={cw}:{ch}:{x}:{y}"
        elif aspect == '16:9':
            target_ratio = 16.0 / 9.0
            current_ratio = w / h
            if current_ratio > target_ratio:
                cw = int(h * target_ratio)
                ch = h
            else:
                cw = w
                ch = int(w / target_ratio)
            x = (w - cw) // 2
            y = (h - ch) // 2
            return f"crop={cw}:{ch}:{x}:{y}"
    except Exception:
        pass
    return ""

def timecode_to_seconds(timecode: str) -> float:
    try:
        timecode = timecode.strip()
        if ':' in timecode:
            parts = timecode.split(':')
            if len(parts) == 3:
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + float(s)
            elif len(parts) == 2:
                m, s = parts
                return int(m) * 60 + float(s)
        return float(timecode)
    except Exception:
        return 0.0

def has_audio_stream(file_path: str) -> bool:
    try:
        cmd = [
            'ffprobe', '-v', 'error', 
            '-show_entries', 'stream=codec_type', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            file_path
        ]
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo, check=True)
        return 'audio' in result.stdout.lower()
    except Exception:
        return False

def get_audio_speed_filter(speed: float) -> str:
    if speed == 1.0:
        return ""
    filters = []
    temp_speed = speed
    while temp_speed > 2.0:
        filters.append("atempo=2.0")
        temp_speed /= 2.0
    while temp_speed < 0.5:
        filters.append("atempo=0.5")
        temp_speed /= 0.5
    if temp_speed != 1.0:
        filters.append(f"atempo={temp_speed}")
    return ",".join(filters)


class TimelineComposer:
    """
    Onyx Multi-Track Timeline Composer Engine v3.0
    -----------------------------------------
    Compiles multiple video segments and images sequentially with visual cropping,
    custom color grading parameters, individual volume levels, silent track fallbacks,
    and multiple overlapping/delayed audio track overlays mixed dynamically.
    """

    def compile_timeline(self, master_audio: str, clips: list, canvas_width: int, canvas_height: int, resize_mode: str, audio_mix_mode: str, master_volume: float, output_path: str, audio_overlays: list = None) -> bool:
        """
        Compiles the B-roll overlay timeline.
        
        Args:
            master_audio (str): Path to single background audio track (legacy/fallback).
            clips (list): List of clip dicts. Each dict contains:
                {
                    'file': str (path),
                    'start': str (HH:MM:SS.mmm),
                    'end': str (HH:MM:SS.mmm),
                    'speed': float (e.g. 0.5, 1.0, 2.0),
                    'volume': float (0.0 to 2.0),
                    'duration': float (used for images),
                    'crop_aspect': str ('None', '1:1', '9:16', '16:9'),
                    'brightness': float (-1.0 to 1.0),
                    'contrast': float (0.0 to 10.0),
                    'saturation': float (0.0 to 3.0),
                    'gamma': float (0.1 to 10.0)
                }
            canvas_width (int): Target width.
            canvas_height (int): Target height.
            resize_mode (str): 'fit' (letterbox) or 'fill' (crop).
            audio_mix_mode (str): 'replace', 'keep_only', or 'mix'.
            master_volume (float): Master volume scaling coefficient (legacy).
            output_path (str): Final rendered file output path.
            audio_overlays (list): List of audio overlay dicts. Each dict contains:
                {
                    'file': str (path),
                    'offset': float (timeline start offset in seconds),
                    'volume': float (0.0 to 2.0)
                }
        """
        if not clips:
            print("❌ Error: No timeline clips provided to compile.")
            return False

        temp_files = []
        temp_dir = tempfile.gettempdir()
        
        print(f"🎬 Onyx Timeline Composer: Initializing render ({len(clips)} clips)...")
        print(f"📐 Target Resolution: {canvas_width}x{canvas_height} | Mode: {resize_mode.upper()} | Mix Mode: {audio_mix_mode.upper()}")

        try:
            # Step 1: Trim, crop, resize, speed-adjust, color-grade, and standardize audio/video for each input clip
            for idx, clip in enumerate(clips):
                clip_path = clip['file']
                speed = clip.get('speed', 1.0)
                volume = clip.get('volume', 1.0)
                crop_aspect = clip.get('crop_aspect', 'None')
                
                # Color grading parameters
                brightness = clip.get('brightness', 0.0)
                contrast = clip.get('contrast', 1.0)
                saturation = clip.get('saturation', 1.0)
                gamma = clip.get('gamma', 1.0)
                
                if not os.path.exists(clip_path):
                    print(f"❌ Error: Clip not found -> {clip_path}")
                    return False
                    
                temp_segment_path = os.path.join(temp_dir, f"onyx_segment_{idx}_{os.path.basename(clip_path)}.mp4")
                temp_files.append(temp_segment_path)
                
                # Check file type
                is_image = clip_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp'))

                # Query media dimensions for cropping calculations
                _, src_w, src_h = get_media_properties(clip_path)
                crop_filter = get_center_crop_filter(src_w, src_h, crop_aspect)

                # Color grading filter
                if brightness != 0.0 or contrast != 1.0 or saturation != 1.0 or gamma != 1.0:
                    eq_filter = f"eq=contrast={contrast}:brightness={brightness}:saturation={saturation}:gamma={gamma}"
                else:
                    eq_filter = ""

                # Build conform scale/pad/crop filters
                if resize_mode == 'fit':
                    scale_filter = f"scale={canvas_width}:{canvas_height}:force_original_aspect_ratio=decrease,pad={canvas_width}:{canvas_height}:(ow-iw)/2:(oh-ih)/2"
                else:
                    scale_filter = f"scale={canvas_width}:{canvas_height}:force_original_aspect_ratio=increase,crop={canvas_width}:{canvas_height}"

                # Combine crop, color grading, and scaling conforms
                video_filters = []
                if crop_filter:
                    video_filters.append(crop_filter)
                if eq_filter:
                    video_filters.append(eq_filter)
                video_filters.append(scale_filter)
                
                combined_video_filter = ",".join(video_filters)

                if is_image:
                    duration = clip.get('duration', 3.0)
                    print(f"⚡ Processing Slide #{idx+1} [IMAGE]: {os.path.basename(clip_path)} | Dur: {duration}s | Crop: {crop_aspect}")
                    
                    # Execute the lavfi (Libavfilter) generator.
                    # 'anullsrc' synthesizes a silent audio stream to satisfy container constraints for imagery.
                    cmd = [
                        'ffmpeg', '-y',
                        '-loop', '1',
                        '-t', str(duration),
                        '-i', clip_path,
                        '-f', 'lavfi',
                        '-t', str(duration),
                        '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
                        '-vf', f"{combined_video_filter},fps=30",
                        '-c:v', SettingsManager.get_video_encoder("libx264"),
                        '-preset', 'fast',
                        '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac',
                        temp_segment_path
                    ]
                else:
                    start = clip.get('start', '00:00:00.000')
                    end = clip.get('end', '00:00:00.000')
                    print(f"⚡ Processing Segment #{idx+1} [VIDEO]: {os.path.basename(clip_path)} | Trim: {start} to {end} | Speed: {speed}x | Vol: {volume:.1f}")

                    # Calculate segment output duration
                    dur_sec = (timecode_to_seconds(end) - timecode_to_seconds(start)) / speed
                    
                    has_audio = has_audio_stream(clip_path)
                    
                    # Standardize audio filters
                    audio_filters = []
                    if speed != 1.0:
                        speed_af = get_audio_speed_filter(speed)
                        if speed_af:
                            audio_filters.append(speed_af)
                    
                    audio_filters.append(f"volume={volume}")
                    audio_filters.append("aresample=44100")
                    audio_filters.append("pan=stereo|FL=c0|FR=c1")
                    af_str = ",".join(audio_filters)

                    if has_audio and volume > 0.01:
                        # Video with active audio stream
                        cmd = [
                            'ffmpeg', '-y',
                            '-ss', str(start),
                            '-to', str(end),
                            '-i', clip_path,
                            '-vf', f"{combined_video_filter},setpts={1.0/speed}*PTS,fps=30",
                            '-af', af_str,
                            '-c:v', SettingsManager.get_video_encoder("libx264"),
                            '-preset', 'fast',
                            '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac',
                            temp_segment_path
                        ]
                    else:
                        # Video has no audio or is muted - merge with silent generator
                        cmd = [
                            'ffmpeg', '-y',
                            '-ss', str(start),
                            '-to', str(end),
                            '-i', clip_path,
                            '-f', 'lavfi',
                            '-t', f"{dur_sec:.3f}",
                            '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
                            '-filter_complex', f"[0:v]{combined_video_filter},setpts={1.0/speed}*PTS,fps=30[v]",
                            '-map', '[v]',
                            '-map', '1:a',
                            '-c:v', SettingsManager.get_video_encoder("libx264"),
                            '-preset', 'fast',
                            '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac',
                            temp_segment_path
                        ]

                # Run standardization
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                subprocess.run(cmd, check=True, startupinfo=startupinfo)

            # Step 2: Create concat description file
            concat_list_path = os.path.join(temp_dir, "onyx_timeline_concat.txt")
            temp_files.append(concat_list_path)
            
            with open(concat_list_path, "w", encoding="utf-8") as f:
                for tf in temp_files[:-1]: # Skip the concat txt file itself
                    safe_path = tf.replace("\\", "/")
                    f.write(f"file '{safe_path}'\n")

            # Concat demuxer output path
            temp_concat_video = os.path.join(temp_dir, "onyx_timeline_concat_out.mp4")
            temp_files.append(temp_concat_video)

            print("🧵 Stitching segments into continuous video stream...")
            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_list_path,
                '-c', 'copy',
                temp_concat_video
            ]
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            subprocess.run(concat_cmd, check=True, startupinfo=startupinfo)

            # Step 3: Mux final video with multiple background audio track overlays (with delay / offsets)
            valid_overlays = []
            
            # 1. Add modern multi-audio overlays if provided
            if audio_overlays:
                for aud in audio_overlays:
                    aud_path = aud['file']
                    if os.path.exists(aud_path):
                        valid_overlays.append({
                            'file': aud_path,
                            'offset': aud.get('offset', 0.0),
                            'volume': aud.get('volume', 1.0)
                        })
            
            # 2. Backward compatibility fallback for single master audio
            if master_audio and os.path.exists(master_audio) and not valid_overlays:
                valid_overlays.append({
                    'file': master_audio,
                    'offset': 0.0,
                    'volume': master_volume
                })

            if valid_overlays and audio_mix_mode != 'keep_only':
                print(f"🔊 Overlaying and mixing {len(valid_overlays)} background audio tracks...")
                
                mux_cmd = ['ffmpeg', '-y', '-i', temp_concat_video]
                for aud in valid_overlays:
                    mux_cmd.extend(['-i', aud['file']])
                    
                filter_parts = []
                mix_inputs = []
                
                # Mix video segments' native audio track
                if audio_mix_mode == 'mix':
                    filter_parts.append("[0:a]volume=1.0[a0]")
                    mix_inputs.append("[a0]")
                    
                for i, aud in enumerate(valid_overlays, start=1):
                    delay_ms = int(aud['offset'] * 1000)
                    vol = aud['volume']
                    # Apply delay and volume filters per track channel
                    filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms},volume={vol}[a{i}]")
                    mix_inputs.append(f"[a{i}]")
                    
                num_inputs = len(mix_inputs)
                if num_inputs > 1:
                    mix_str = "".join(mix_inputs)
                    # Dynamically construct the 'amix' filter graph.
                    # 'duration=first' anchors the output duration to the primary video stream.
                    # 'dropout_transition=2' smooths volume normalization shifts when overlays terminate.
                    filter_parts.append(f"{mix_str}amix=inputs={num_inputs}:duration=first:dropout_transition=2[a]")
                    audio_map = "[a]"
                elif num_inputs == 1:
                    audio_map = mix_inputs[0]
                else:
                    audio_map = "[a]"
                    filter_parts.append("anullsrc=channel_layout=stereo:sample_rate=44100[a]")
                    
                mux_cmd.extend([
                    '-filter_complex', ";".join(filter_parts),
                    '-map', '0:v:0',
                    '-map', audio_map,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-shortest',
                    output_path
                ])
                subprocess.run(mux_cmd, check=True, startupinfo=startupinfo)
            else:
                # Keep only clip audios or no background audio tracks are loaded
                print("🔇 Retaining original clip audios only. Rendering final timeline output...")
                import shutil
                shutil.copy2(temp_concat_video, output_path)

            print(f"🎉 RENDER COMPLETE! Output compiled successfully to: {output_path}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg error during compilation: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ System error during timeline rendering: {str(e)}")
            return False
            
        finally:
            # Clean up all temporary files safely
            print("🧹 Cleaning up temporary workspace files...")
            for tf in temp_files:
                if os.path.exists(tf):
                    try:
                        os.remove(tf)
                    except Exception:
                        pass


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.timeline_composer import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (timeline_composer.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'timeline_composer.py', is a core component of the Onyx Engine. It is
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
