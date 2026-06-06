import os
import glob

ui_dir = 'src/ui'
files = glob.glob(os.path.join(ui_dir, '*_ui.py'))

to_replace = [
    'QPushButton("🔄 Convert Format")',
    'QPushButton("🔨 Split Tracks")',
    'QPushButton("🎬 Suture Files Together")',
    'QPushButton("🎬 Stitch Media")',
    'QPushButton("🎬 Start Merging")',
    'QPushButton("🎬 Execute Composite")',
    'QPushButton("✨ Start 4K AI Remastering")',
    'QPushButton("🏎️ Execute FlowFrames")',
    'QPushButton("🧠 Process with AI Engine")',
    'QPushButton("⚖️ Run Gyro-Stabilization")',
    'QPushButton("🎵 Extract Audio")',
    'QPushButton("🎵 Batch Extract All")',
    'QPushButton("✍️ Generate Transcript")',
    'QPushButton("🔥 Burn Watermark")',
    'QPushButton("✨ Execute De-Watermark")',
    'QPushButton("🎬 Generate GIF")',
    'QPushButton("🎨 Apply Grading")'
]

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = content
    for text in to_replace:
        if text in modified:
            modified = modified.replace(text, text.replace('QPushButton', 'SmartRunButton'))
            
    if modified != content:
        if 'SmartRunButton' not in modified and 'from src.ui.custom_widgets import DropZone' in modified:
            modified = modified.replace('import DropZone', 'import DropZone, SmartRunButton')
        elif 'SmartRunButton' not in modified:
            modified = 'from src.ui.custom_widgets import SmartRunButton\n' + modified
            
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(modified)
        print(f'Updated {os.path.basename(fpath)}')
