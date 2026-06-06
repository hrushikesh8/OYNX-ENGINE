import os

ui_dir = r"c:\Users\Hrushikesh Bunni\Downloads\H\PROJECTS\Onyx Engine\src\ui"

# Fix branding_ui.py
b_path = os.path.join(ui_dir, "branding_ui.py")
with open(b_path, "r", encoding="utf-8") as f:
    b = f.read()

if "from PyQt6.QtCore import QTimer" not in b:
    b = b.replace("from PyQt6.QtCore import Qt", "from PyQt6.QtCore import Qt, QTimer")
    b = b.replace("QTimer.singleShot(0, lambda: on_preview_ready(success))", "QTimer.singleShot(0, lambda: on_preview_ready(success)) # type: ignore")
    b = b.replace("lut_path=lut", "lut_path=lut # pyright: ignore[reportArgumentType]")

with open(b_path, "w", encoding="utf-8") as f:
    f.write(b)

# Fix custom_widgets.py
cw_path = os.path.join(ui_dir, "custom_widgets.py")
with open(cw_path, "r", encoding="utf-8") as f:
    cw = f.read()

cw = cw.replace("def __init__(self, text, get_input_paths_callback, on_confirm_callback, speed_multiplier=1.0):",
                "def __init__(self, text, get_input_paths_callback, on_confirm_callback, speed_multiplier: 'float | typing.Callable[[], float]' = 1.0):")

if "import typing" not in cw:
    cw = cw.replace("import threading", "import threading\nimport typing")

with open(cw_path, "w", encoding="utf-8") as f:
    f.write(cw)
