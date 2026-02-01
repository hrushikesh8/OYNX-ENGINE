import os
import sys
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
        filename = Path(input_path).stem
        output_path = os.path.join(output_folder, f"{filename}.{target_format}")
        
        # Get flags from our rules, default to simple copy if unknown
        cmd_flags = self.FORMAT_RULES.get(target_format, ['-c', 'copy'])

        print(f"🔄 Converting: {filename} -> .{target_format}")
        
        command = ['ffmpeg', '-i', input_path, *cmd_flags, '-y', output_path]
        
        try:
            # Run ffmpeg (capture_output=True hides spam, set to False to see progress)
            subprocess.run(command, check=True, capture_output=True)
            return {"status": "success", "file": filename}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "file": filename, "message": str(e)}

    def process_input(self, input_path: str, output_folder: str, target_format: str):
        """Decides whether to process a single file or a folder."""
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        tasks = []
        
        # Check if input is a directory or a file
        if os.path.isdir(input_path):
            print(f"📂 Detected folder. Scanning for video files...")
            # Recursive search for video files
            extensions = ('*.mp4', '*.mkv', '*.avi', '*.mov', '*.flv', '*.wmv')
            for ext in extensions:
                tasks.extend(glob.glob(os.path.join(input_path, '**', ext), recursive=True))
        elif os.path.isfile(input_path):
            print(f"📄 Detected single file.")
            tasks = [input_path]
        else:
            print("❌ Error: Invalid input path.")
            return

        if not tasks:
            print("❌ No video files found.")
            return

        print(f"🚀 Starting batch processing for {len(tasks)} files...")
        print("-" * 40)

        success_count = 0
        error_count = 0

        for file_path in tasks:
            # Skip if the file is already in the target format to prevent overwriting/loops
            if file_path.lower().endswith(f".{target_format}"):
                print(f"⏭️  Skipping {os.path.basename(file_path)} (already in target format)")
                continue

            result = self.convert_video(file_path, output_folder, target_format)
            
            if result['status'] == 'success':
                print(f"✅ Done: {result['file']}")
                success_count += 1
            else:
                print(f"❌ Failed: {result['file']}")
                error_count += 1

        print("-" * 40)
        print(f"🎉 Batch Complete. Success: {success_count} | Errors: {error_count}")


def interactive_menu():
    """Shows a menu if no arguments are provided."""
    print("\n🎬 --- VidFlow Video Converter ---")
    
    # 1. Get Input
    input_path = input("Enter Input Path (Folder or File): ").strip().strip('"')
    if not os.path.exists(input_path):
        print("❌ Path does not exist!")
        return

    # 2. Get Output
    output_path = input("Enter Output Folder (leave blank for 'converted' folder): ").strip().strip('"')
    if not output_path:
        output_path = os.path.join(os.path.dirname(input_path) if os.path.isfile(input_path) else input_path, "converted")

    # 3. Choose Format
    print("\nAvailable Formats:")
    formats = list(FormatMapper.FORMAT_RULES.keys())
    for i, fmt in enumerate(formats, 1):
        print(f"{i}. {fmt.upper()}")
    
    choice = input("Select format number (default 2 [MP4]): ")
    try:
        target_format = formats[int(choice) - 1]
    except (ValueError, IndexError):
        target_format = 'mp4'

    print(f"\nSelected: Input={input_path}, Format={target_format.upper()}")
    FormatMapper().process_input(input_path, output_path, target_format)


if __name__ == "__main__":
    # If arguments are provided, use CLI mode
    if len(sys.argv) >= 3:
        input_arg = sys.argv[1]
        format_arg = sys.argv[2]
        # Default output folder is same as input parent if not specified
        output_arg = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(input_arg), "converted")
        
        FormatMapper().process_input(input_arg, output_arg, format_arg)
    
    # Otherwise, switch to interactive menu mode
    else:
        interactive_menu()