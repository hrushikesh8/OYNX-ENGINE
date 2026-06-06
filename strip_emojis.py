import os
import re

processors_dir = r"c:\Users\Hrushikesh Bunni\Downloads\H\PROJECTS\Onyx Engine\src\processors"

# We want to remove all emojis (characters outside the basic ASCII/extended range, specifically unicode emojis).
# A simple regex to strip out non-ASCII characters from print statements:
# But it's safer to just strip any character > \uFFFF or specifically known emojis.
# Let's use a regex to target print statements and remove characters > \u007F (non-ASCII)

for filename in os.listdir(processors_dir):
    if not filename.endswith(".py"):
        continue
    filepath = os.path.join(processors_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find all print statements
    def replacer(match):
        text = match.group(0)
        # Remove any character that is an emoji (usually > 0x2000)
        # We can just remove everything > \u007f to be safe, except we might want some?
        # Actually, let's just remove anything outside the standard ASCII range in prints
        cleaned = re.sub(r'[^\x00-\x7F]+', '', text)
        return cleaned

    new_content = re.sub(r'print\(f?["\'].*?["\']\)', replacer, content)
    
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Cleaned {filename}")
