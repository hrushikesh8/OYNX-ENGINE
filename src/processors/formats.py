import os
import subprocess
from pathlib import Path
import glob

class FormatMapper:
    # Define codec rules for different containers to ensure compatibility
    FORMAT_RULES = {
        'mkv': ['-map', '0', '-c', 'copy'],  # Lossless, keeps all streams
        'mp4': ['-c:v', 'copy', '-c:a', 'aac', '-c:s', 'mov_text', '-strict', 'experimental'], # Best for compatibility
        'avi': ['-c:v', 'copy', '-c:a', 'copy'],
        'mov': ['-c:v', 'copy', '-c:a', 'aac'],
        'flv': ['-c:v', 'flv', '-c:a', 'aac'],
        'webm': ['-c:v', 'libvpx-vp9', '-c:a', 'libopus'],  # WebM usually needs re-encoding
    }

    def convert_video(self, input_path: str, output_folder: str, target_format: str) -> dict:
        """Helper function to convert a single file."""
        filename = Path(input_path).stem
        output_path = os.path.join(output_folder, f"{filename}.{target_format}")
        
        # Get flags from our rules, default to simple copy if unknown
        cmd_flags = self.FORMAT_RULES.get(target_format, ['-c', 'copy'])

        print(f"   🔄 Converting: {filename} -> .{target_format}")
        
        command = ['ffmpeg', '-i', input_path, *cmd_flags, '-y', output_path]
        
        try:
            # Run ffmpeg (capture_output=True hides spam)
            subprocess.run(command, check=True, capture_output=True)
            return {"status": "success", "file": filename}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "file": filename, "message": str(e)}

    def process_input(self, input_path: str, output_folder: str, target_format: str):
        """
        Smart Processor: Handles both Single Files and Folders (Batch).
        """
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        tasks = []
        
        # 1. Detect Input Type
        if os.path.isdir(input_path):
            print(f"📂 Scanning folder for videos...")
            # Recursive search for video files
            extensions = ('*.mp4', '*.mkv', '*.avi', '*.mov', '*.flv', '*.wmv')
            for ext in extensions:
                tasks.extend(glob.glob(os.path.join(input_path, '**', ext), recursive=True))
        
        elif os.path.isfile(input_path):
            tasks = [input_path]
        
        else:
            print("❌ Error: Invalid input path.")
            return

        if not tasks:
            print("❌ No video files found.")
            return

        print(f"🚀 Processing {len(tasks)} files...")
        print("-" * 40)

        success_count = 0
        error_count = 0

        for file_path in tasks:
            # Skip if the file is already in the target format (prevent overwriting/loops)
            if file_path.lower().endswith(f".{target_format}"):
                print(f"   ⏭️  Skipping {os.path.basename(file_path)} (already matches format)")
                continue

            result = self.convert_video(file_path, output_folder, target_format)
            
            if result['status'] == 'success':
                print(f"   ✅ Done: {result['file']}")
                success_count += 1
            else:
                print(f"   ❌ Failed: {result['file']}")
                error_count += 1

        print("-" * 40)
        print(f"🎉 Complete. Success: {success_count} | Errors: {error_count}")

# ==========================================
# HOW TO USE THIS CODE (DOCUMENTATION)
# ==========================================
#
# 1. Import:
#    from src.processors.formats import FormatMapper
#
# 2. Instantiate:
#    converter = FormatMapper()
#
# 3. USE CASE A: Batch Convert a Folder
#    converter.process_input(
#        input_path="C:/Downloads/Movies/", 
#        output_folder="C:/Downloads/Movies/Converted", 
#        target_format="mp4"
#    )
#
# 4. USE CASE B: Convert Single File
#    converter.process_input(
#        input_path="C:/Video.mkv", 
#        output_folder="C:/Converted", 
#        target_format="avi"
#    )
# ==========================================