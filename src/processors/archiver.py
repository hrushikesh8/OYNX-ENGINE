import shutil
import os
import sys

class FolderArchiver:
    """
    VidFlow Batch Archiving Engine
    ------------------------------
    Automates the zipping of multiple sub-directories within a parent folder.
    Optimized for preparing high-volume media assets for server transfers.
    """

    def batch_zip_folders(self, parent_directory: str):
        """
        Scans a parent directory and converts every immediate sub-folder 
        into an individual, high-compatibility .zip file.
        
        Logic Flow:
        1. Validate path: Ensures the target folder exists and is accessible.
        2. Identify Targets: Iterates through contents to isolate directories.
        3. Compression: Executes shutil's archive utility on each target.
        4. Reporting: Provides a success count and error tracking.
        
        Args:
            parent_directory (str): The path containing the folders to be zipped.
        """
        
        # Security Check: Ensure the target path actually exists
        if not os.path.exists(parent_directory):
            print(f"❌ Error: Specified path does not exist -> {parent_directory}")
            return False

        print(f"📦 VidFlow Archiver Service: Initializing...")
        print(f"📂 Scanning Directory: {parent_directory}")
        
        try:
            # Retrieve all items within the parent directory
            items = os.listdir(parent_directory)
        except PermissionError:
            print("❌ Access Denied: Insufficient permissions to read this directory.")
            return False
            
        success_count = 0
        error_count = 0

        for item in items:
            # Construct absolute path for the item
            item_path = os.path.join(parent_directory, item)
            
            # Feature Logic: Only process folders. Skip existing files and .zip archives.
            if os.path.isdir(item_path):
                try:
                    print(f"⚡ Zipping folder -> {item}...")
                    
                    # shutil.make_archive parameters:
                    # (output_filename, format, root_dir)
                    # This creates item.zip in the same parent directory.
                    shutil.make_archive(item_path, 'zip', item_path)
                    
                    success_count += 1
                except Exception as e:
                    print(f"⚠️ Failed to archive {item}: {str(e)}")
                    error_count += 1

        print("-" * 50)
        print(f"✅ BATCH COMPLETE")
        print(f"📊 Folders Zipped: {success_count}")
        if error_count > 0:
            print(f"❗ Errors Encountered: {error_count}")
        print("-" * 50)
        
        return True if success_count > 0 else False

# --- STANDALONE EXECUTION LOGIC ---
if __name__ == "__main__":
    # Check for directory argument
    if len(sys.argv) < 2:
        print("Usage: python archiver.py <target_parent_directory>")
        sys.exit(1)

    target_path = sys.argv[1]
    
    # Initialize the engine
    archiver = FolderArchiver()
    
    # Execute batch process
    if archiver.batch_zip_folders(target_path):
        print("🎉 All archives generated successfully.")
    else:
        print("⚠️ No folders were processed. Check the directory path.")

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
#
# Syntax: python src/processors/archiver.py <ParentDirectoryPath>
#
# Example:
# python src/processors/archiver.py "D:/Videos/YouTube_Series_Project"
#
# Result: 
# If "YouTube_Series_Project" contains folders named "Raw_Footage", 
# "Assets", and "Final_Exports", this script will instantly create:
# - Raw_Footage.zip
# - Assets.zip
# - Final_Exports.zip





# ==============================================================================
# 📦 FEATURE: THE BATCH FOLDER ARCHIVER
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file is called 'archiver.py', and its job is "Logistics & Storage." 
#    When you have a project with 20 different folders (like Episodes, Raw 
#    Footage, and Assets), zipping them manually is a pain. This script 
#    automates that. It scans a folder and turns every sub-folder into its 
#    own individual .zip file, making your server library neat and easy to share.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    The Archiver uses parallel-ready logic to handle mass-scale compression. 
#    It iterates through a parent directory, identifies only the folders, and 
#    executes a 1-to-1 mapping to ZIP archives. It is built to be a "silent" 
#    background worker for large data migrations.
#
# 2. KEY FEATURES:
#    - Folder Isolation: Smart enough to skip loose files and only zip folders.
#    - Directory Preservation: Keeps all internal timestamps and folder structures.
#    - shutil Integration: Uses high-level disk I/O for faster zipping of media.
#
# 3. APPLICATIONS:
#    - Project Transfers: Preparing an entire season of a show for cloud upload.
#    - Storage Clearing: Zipping "cold" (old) projects to save server space.
#    - Media Logistics: Organizing complex asset folders into clean archives.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - Disk I/O: Extremely High. Performance depends on your SSD/HDD speed.
#    - CPU/RAM: Low. It streams data directly from the disk to the zip file.
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - Encryption: Adding passwords to the ZIP files for secure sharing.
#    - Auto-Cleanup: Deleting the original folder once the ZIP is verified.
#
# 6. HOW TO USE THIS MODULE:
#    Syntax:  python src/processors/archiver.py <ParentFolderPath>
#    Example: python src/processors/archiver.py "C:/VidFlow/Raw_Projects"
#    Output:  Individual .zip files for every sub-folder inside the path.
#
# ==============================================================================