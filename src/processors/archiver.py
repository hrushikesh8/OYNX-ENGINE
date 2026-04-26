import os
import sys
import zipfile

class FolderArchiver:
    """
    VidFlow Batch Archiving Engine
    ------------------------------
    Automates the zipping of multiple sub-directories within a parent folder.
    Optimized for preparing high-volume media assets for server transfers.
    """

    def batch_zip_folders(self, parent_directory: str, compress: bool = False):
        """
        Scans a parent directory and converts every immediate sub-folder 
        into an individual .zip file.
        
        Args:
            parent_directory (str): The path containing the folders to be zipped.
            compress (bool): If True, uses DEFLATE compression. If False, uses 
                             STORE mode for maximum packaging speed (best for video).
        """
        
        # Security Check: Ensure the target path actually exists
        if not os.path.exists(parent_directory):
            print(f"❌ Error: Specified path does not exist -> {parent_directory}")
            return False

        # Set the dynamic UI string and Zip Mode based on user choice
        mode_str = "High-Compression Mode" if compress else "High-Speed Store Mode"
        zip_engine = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED

        print(f"📦 VidFlow Archiver Service: Initializing ({mode_str})...")
        print(f"📂 Scanning Directory: {parent_directory}")
        
        try:
            items = os.listdir(parent_directory)
        except PermissionError:
            print("❌ Access Denied: Insufficient permissions to read this directory.")
            return False
            
        success_count = 0
        error_count = 0

        for item in items:
            item_path = os.path.join(parent_directory, item)
            
            if os.path.isdir(item_path):
                try:
                    action_verb = "Compressing" if compress else "Packaging"
                    print(f"⚡ {action_verb} folder -> {item}...")
                    
                    zip_file_path = f"{item_path}.zip"
                    
                    # 🚀 DUAL-MODE ENGINE: Uses whatever engine the user selected
                    with zipfile.ZipFile(zip_file_path, 'w', zip_engine) as zipf:
                        for root, _, files in os.walk(item_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                archive_name = os.path.relpath(file_path, item_path)
                                zipf.write(file_path, archive_name)
                    
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
    if len(sys.argv) < 2:
        print("Usage: python archiver.py <target_parent_directory> [compress: y/n]")
        sys.exit(1)

    target_path = sys.argv[1]
    do_compress = True if (len(sys.argv) > 2 and sys.argv[2].lower() == 'y') else False
    
    archiver = FolderArchiver()
    if archiver.batch_zip_folders(target_path, compress=do_compress):
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
# 📦 FEATURE: THE BATCH FOLDER ARCHIVER (DUAL-MODE)
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
#    The Archiver uses parallel-ready logic to handle mass-scale packaging. 
#    It iterates through a parent directory, identifies only the folders, and 
#    executes a 1-to-1 mapping to ZIP archives using 'Store Mode' (ZIP_STORED)
#    to bypass unnecessary compression math on already-compressed media files.
#
# 2. KEY FEATURES:
#    - Folder Isolation: Smart enough to skip loose files and only zip folders.
#    - Directory Preservation: Keeps all internal timestamps and folder structures.
#    - Native Packaging: Uses high-level disk I/O for lightning-fast bundling.
#
# 3. APPLICATIONS:
#    - Project Transfers: Preparing an entire season of a show for cloud upload.
#    - Storage Clearing: Zipping "cold" (old) projects to save server space.
#    - Media Logistics: Organizing complex asset folders into clean archives.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - Disk I/O: Extremely High. Performance depends entirely on your SSD/HDD speed.
#    - CPU/RAM: Near zero. Bypasses compression to stream data directly to the zip.
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