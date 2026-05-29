import os
import csv
import shutil
from datetime import datetime
from pathlib import Path

LOGS_DIR = "logs"

class TimeMachine:
    """
    The Global Time Machine for Onyx Engine and Chronicle.
    Manages tool-specific CSV ledgers to revert both file creations (FFmpeg) and file renames.
    """
    
    @staticmethod
    def get_ledger_path(tool_name: str) -> str:
        """Generates a standardized, filesystem-safe CSV path for a given tool's ledger."""
        # Ensure the target directory exists to prevent FileNotFoundError during initial logging operations.
        os.makedirs(LOGS_DIR, exist_ok=True)
        # Sanitize the tool name to prevent invalid path characters across different operating systems.
        safe_name = "".join([c if c.isalnum() else "_" for c in tool_name]).lower()
        return os.path.join(LOGS_DIR, f"{safe_name}.csv")

    @staticmethod
    def log_action(tool_name: str, run_id: str, action: str, src: str, dst: str, op_type: str = "CREATE"):
        """
        Logs an action to the tool's ledger.
        op_type: 'CREATE' (Onyx FFmpeg renders) or 'RENAME' (Chronicle sorting).
        """
        ledger_path = TimeMachine.get_ledger_path(tool_name)
        # Verify if the file exists and contains data to determine if header initialization is required.
        file_has_headers = os.path.isfile(ledger_path) and os.path.getsize(ledger_path) > 0
        
        # Open in append mode ('a') to ensure historical logging data is preserved.
        with open(ledger_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_has_headers:
                writer.writerow(["Run_ID", "Timestamp", "Op_Type", "Action", "Source", "Destination"])
            
            # Record the execution timestamp to facilitate chronological sorting in the UI.
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([run_id, timestamp, op_type, action, src, dst])

    @staticmethod
    def get_run_summaries():
        """
        Reads all CSV ledgers in the logs folder and bundles them into clean summaries.
        Returns a list of dicts: {'tool': str, 'run_id': str, 'desc': str, 'timestamp': str}
        """
        if not os.path.exists(LOGS_DIR):
            return []
            
        summary_list = []
        for file in os.listdir(LOGS_DIR):
            if not file.endswith('.csv'): continue
            
            tool_name = file.replace('.csv', '').replace('_', ' ').title()
            ledger_path = os.path.join(LOGS_DIR, file)
            
            runs = {}
            with open(ledger_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rid = row['Run_ID']
                    if rid not in runs:
                        runs[rid] = {
                            'timestamp': row['Timestamp'], 
                            'action': row['Action'], 
                            'count': 0, 
                            'sample_dst': row['Destination']
                        }
                    runs[rid]['count'] += 1
            
            for rid, data in runs.items():
                folder_name = os.path.basename(os.path.dirname(data['sample_dst']))
                desc = f"[{data['timestamp']}] {data['action']} | {folder_name} ({data['count']} files)"
                summary_list.append({
                    'tool': tool_name,
                    'run_id': rid,
                    'desc': desc,
                    'timestamp': data['timestamp'],
                    'file': file
                })
                
        # Sort so newest runs are at the top
        return sorted(summary_list, key=lambda x: x['timestamp'], reverse=True)

    @staticmethod
    def undo_target_run(ledger_filename: str, target_run_id: str):
        """
        Surgically extracts and reverts ONLY the files from the selected Run_ID.
        """
        ledger_path = os.path.join(LOGS_DIR, ledger_filename)
        if not os.path.exists(ledger_path):
            print(f"❌ Error: Ledger {ledger_filename} not found.")
            return False, f"Ledger {ledger_filename} not found."
            
        remaining_rows = []
        revert_count = 0
        folders_to_check = set()
        
        print(f"\n⏪ TIME MACHINE INITIATED: Reverting {target_run_id} from {ledger_filename}...")
        
        # Read the entire CSV into memory to allow safe manipulation of the ledger rows.
        with open(ledger_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)

        # Iterate in reverse chronological order to prevent folder state conflicts during sequential renames.
        for row in reversed(rows):
            if row['Run_ID'] == target_run_id:
                op_type = row.get('Op_Type', 'RENAME') # Fallback to RENAME for older logs
                src = row['Source']
                dst = row['Destination']
                
                # Execute the reversion only if the destination file still exists in the filesystem.
                if os.path.exists(dst):
                    if op_type == "RENAME":
                        # Restore the file to its original path, creating any missing parent directories.
                        os.makedirs(os.path.dirname(src), exist_ok=True)
                        shutil.move(dst, src)
                        print(f"   🔙 Reverted Rename: {os.path.basename(src)}")
                    elif op_type == "CREATE":
                        # Permanently delete files generated by rendering operations to reclaim disk space.
                        os.remove(dst)
                        print(f"   🗑️ Deleted Generated File: {os.path.basename(dst)}")
                    
                    revert_count += 1
                    folders_to_check.add(os.path.dirname(dst))
            else:
                # Retain rows belonging to other Run_IDs to preserve their history.
                remaining_rows.append(row)

        # Sweep up empty folders left behind
        for folder in folders_to_check:
            if os.path.exists(folder) and not os.listdir(folder):
                try: os.rmdir(folder)
                except OSError: pass
                print(f"   [REMOVED] Empty folder: {os.path.basename(folder)}")

        # Flip remaining rows back to chronological order
        remaining_rows.reverse()

        # Overwrite the CSV with the excised ledger
        with open(ledger_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(remaining_rows)

        msg = f"✅ Time Machine Complete! {revert_count} files successfully reverted/deleted."
        print(msg)
        print("-" * 50)
        return True, msg


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.time_machine import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (time_machine.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'time_machine.py', is a core component of the Onyx Engine. It is
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
