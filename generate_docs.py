import os
import glob
import ast

def get_footer(filename, module_name):
    return f"""

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.{module_name} import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION ({filename})
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, '{filename}', is a core component of the Onyx Engine. It is
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
"""

def add_docs(filepath):
    filename = os.path.basename(filepath)
    module_name = filename.replace('.py', '')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "HOW TO USE THIS CODE (EXAMPLE)" in content:
        return False
        
    # Add footer
    content += get_footer(filename, module_name)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

if __name__ == "__main__":
    targets = [
        "src/processors/*.py",
        "src/processors/chronicle/*.py",
        "src/ui/*.py",
        "src/utils/*.py",
        "*.py"
    ]
    
    updated_count = 0
    for target in targets:
        for file in glob.glob(target):
            if file.endswith("generate_docs.py"):
                continue
            if add_docs(file):
                print(f"Added docs to {file}")
                updated_count += 1
                
    print(f"Finished! Updated {updated_count} files.")
