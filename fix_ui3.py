import os

ui_dir = r"c:\Users\Hrushikesh Bunni\Downloads\H\PROJECTS\Onyx Engine\src\ui"
b_path = os.path.join(ui_dir, "branding_ui.py")

with open(b_path, "r", encoding="utf-8") as f:
    b = f.read()

# Fix the comment inside parenthesis bug
b = b.replace("lut_path=lut # pyright: ignore[reportArgumentType])", "lut_path=lut) # pyright: ignore[reportArgumentType]")

with open(b_path, "w", encoding="utf-8") as f:
    f.write(b)
