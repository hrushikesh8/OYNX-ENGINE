import os
import re

ui_dir = r"c:\Users\Hrushikesh Bunni\Downloads\H\PROJECTS\Onyx Engine\src\ui"

# Fix title_bar.py
t_path = os.path.join(ui_dir, "title_bar.py")
with open(t_path, "r", encoding="utf-8") as f:
    t = f.read()

t = re.sub(r'\bself\.parent\b', 'self.main_window', t)
with open(t_path, "w", encoding="utf-8") as f:
    f.write(t)

# Fix tracks_ui.py basename None issue
tr_path = os.path.join(ui_dir, "tracks_ui.py")
with open(tr_path, "r", encoding="utf-8") as f:
    tr = f.read()

tr = tr.replace("name, _ = os.path.splitext(os.path.basename(path))",
                "name, _ = os.path.splitext(os.path.basename(path if path else ''))")

with open(tr_path, "w", encoding="utf-8") as f:
    f.write(tr)
