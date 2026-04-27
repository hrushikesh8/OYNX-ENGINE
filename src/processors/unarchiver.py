import os
import subprocess

class EnterpriseUnarchiver:
    """
    VidFlow High-Speed Un-Archiver
    ------------------------------
    Bypasses Windows entirely by hooking directly into the 7-Zip C++ binary.
    Immune to the Windows 260-character limit.
    """
    
    def __init__(self):
        # We point Python exactly to where you dropped the .exe
        self.engine_path = os.path.abspath(os.path.join("src", "tools", "7za.exe"))

    def extract_archive(self, zip_path: str, output_folder: str = None):
        """
        Uses 7za.exe to blast open a zip file at maximum disk speed.
        """
        if not os.path.exists(self.engine_path):
            print("❌ CRITICAL: 7za.exe not found in src/tools/")
            print("Please download it and place it in the tools folder.")
            return False

        if not os.path.exists(zip_path):
            print(f"❌ Error: Could not find archive -> {zip_path}")
            return False

        # If user doesn't specify an output folder, extract it right next to the zip
        if not output_folder:
            output_folder = os.path.splitext(zip_path)[0]

        print(f"🚀 VidFlow Un-Archiver: Firing up 7-Zip Engine...")
        print(f"📦 Target: {os.path.basename(zip_path)}")
        print(f"📂 Dest: {output_folder}")

        # --- THE 7-ZIP COMMAND ---
        # x  = Extract with full paths
        # -o = Output directory (must be attached to the path, no space)
        # -y = Assume "Yes" to all prompts (don't pause the script)
        command = [
            self.engine_path, 
            'x', zip_path, 
            f'-o{output_folder}', 
            '-y'
        ]

        try:
            # We run the .exe and capture the output so it doesn't spam the terminal
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print("-" * 50)
            print("✅ EXTRACTION COMPLETE (Windows Bypassed)")
            print("-" * 50)
            return True
        except subprocess.CalledProcessError as e:
            print("❌ Extraction Failed!")
            print(e.stderr)
            return False