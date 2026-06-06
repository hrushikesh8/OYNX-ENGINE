import os
import re

ui_dir = r"c:\Users\Hrushikesh Bunni\Downloads\H\PROJECTS\Onyx Engine\src\ui"

for filename in os.listdir(ui_dir):
    if not filename.endswith(".py"):
        continue
    filepath = os.path.join(ui_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    original = content
    
    # Fix self.layout shadowing QWidget.layout()
    content = re.sub(r'self\.layout\b', 'self.main_layout', content)
    
    # Fix self.scroll shadowing QWidget.scroll()
    content = re.sub(r'self\.scroll\b', 'self.scroll_area', content)
    
    # Fix Qt.EasingCurve -> QEasingCurve
    content = re.sub(r'Qt\.EasingCurve', 'QEasingCurve', content)
    
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {filename}")

# Fix specific things in custom_widgets.py
cw_path = os.path.join(ui_dir, "custom_widgets.py")
with open(cw_path, "r", encoding="utf-8") as f:
    cw = f.read()

# Fix QEasingCurve import
if "QEasingCurve" not in cw:
    cw = cw.replace("from PyQt6.QtCore import QTimer, QPropertyAnimation, QRect", 
                    "from PyQt6.QtCore import QTimer, QPropertyAnimation, QRect, QEasingCurve")

# Fix _TextIOBase.write return type
cw = cw.replace("def write(self, message):", "def write(self, message) -> int:")
cw = cw.replace("super().write(message)", "return super().write(message)")

with open(cw_path, "w", encoding="utf-8") as f:
    f.write(cw)

# Fix specific things in branding_ui.py
b_path = os.path.join(ui_dir, "branding_ui.py")
with open(b_path, "r", encoding="utf-8") as f:
    b = f.read()

# Fix timestamp int cast
b = b.replace("coords = get_watermark_coords(vid, timestamp=pos_sec)", 
              "coords = get_watermark_coords(vid, timestamp=int(pos_sec))")

with open(b_path, "w", encoding="utf-8") as f:
    f.write(b)
