import os
import subprocess
import json

class AspectCropper:
    def __init__(self):
        pass

    def get_video_dimensions(self, video_path):
        """Uses ffprobe to get the width and height of a video."""
        cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height', '-of', 'json', video_path
        ]
        
        # Hide console window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
            info = json.loads(result.stdout)
            width = info['programs'][0]['streams'][0]['width'] if 'programs' in info else info['streams'][0]['width']
            height = info['programs'][0]['streams'][0]['height'] if 'programs' in info else info['streams'][0]['height']
            return int(width), int(height)
        except Exception as e:
            print(f"Error getting dimensions: {e}")
            return None, None

    def crop_video(self, input_path, output_path, aspect_ratio="9:16", position="center", custom_coords=None, start_time=None, duration=None):
        """
        Crops a video to the specified aspect ratio.
        aspect_ratio: "9:16", "1:1", "4:3", "16:9", or "custom"
        position: "center", "left", "right", or "custom"
        custom_coords: tuple of (x, y, w, h) if position is custom
        """
        if position == "custom" and custom_coords:
            x, y, w, h = custom_coords
            crop_filter = f"crop={w}:{h}:{x}:{y}"
        else:
            in_w, in_h = self.get_video_dimensions(input_path)
            if not in_w or not in_h:
                print("Failed to read input video dimensions.")
                return False, "Failed to read input video dimensions."
                
            # Parse target aspect ratio
            if ":" in aspect_ratio:
                ar_w, ar_h = map(float, aspect_ratio.split(":"))
                target_ar = ar_w / ar_h
            else:
                target_ar = in_w / in_h # fallback to original
                
            current_ar = in_w / in_h
            
            # Calculate output width and height
            if current_ar > target_ar:
                # Video is wider than target. Keep height, crop width.
                out_h = in_h
                out_w = int(in_h * target_ar)
                
                # Ensure even dimensions for ffmpeg compatibility
                out_w = out_w - (out_w % 2)
            else:
                # Video is taller than target. Keep width, crop height.
                out_w = in_w
                out_h = int(in_w / target_ar)
                
                # Ensure even dimensions
                out_h = out_h - (out_h % 2)
                
            # Calculate x, y based on position
            if position == "center":
                x = (in_w - out_w) // 2
                y = (in_h - out_h) // 2
            elif position == "left":
                x = 0
                y = (in_h - out_h) // 2
            elif position == "right":
                x = in_w - out_w
                y = (in_h - out_h) // 2
            else:
                x = (in_w - out_w) // 2
                y = (in_h - out_h) // 2
                
            crop_filter = f"crop={out_w}:{out_h}:{x}:{y}"
            
        print(f" Applying crop filter: {crop_filter}")
        
        cmd = ['ffmpeg', '-y']
        
        if start_time:
            cmd.extend(['-ss', start_time])
        if duration:
            cmd.extend(['-t', duration])
            
        cmd.extend([
            '-i', input_path,
            '-vf', crop_filter,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
            '-c:a', 'copy',
            output_path
        ])
        
        print(f"Running command: {' '.join(cmd)}")
        
        # Hide console window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        try:
            # We don't need to block UI, MasterOrchestrator's TaskWorker handles the background running
            # But since TaskWorker calls this function synchronously in its thread, we just use subprocess.run
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, startupinfo=startupinfo)
            if process.returncode == 0:
                print(f" Successfully cropped video to {output_path}")
                return True, "Crop completed successfully."
            else:
                print(f" FFmpeg error:\n{process.stdout}")
                return False, "FFmpeg processing failed."
        except Exception as e:
            print(f" Python error: {e}")
            return False, f"Python error: {e}"
