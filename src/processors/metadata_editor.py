import subprocess
import json
import os

class MetadataEditor:
    """
    VidFlow Container Metadata Tag Editor
    --------------------------------------
    Uses ffprobe to extract global container tags (Title, Artist, Genre, etc.)
    and FFmpeg stream copy to write updated tags instantly.
    """
    def read_metadata(self, input_path: str) -> dict:
        """Reads global metadata tags from a video file."""
        if not os.path.exists(input_path):
            return {}

        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format',
            '-of', 'json',
            input_path
        ]
        try:
            output = subprocess.check_output(cmd)
            data = json.loads(output)
            return data.get('format', {}).get('tags', {})
        except Exception as e:
            print(f"❌ Error reading metadata tags: {e}")
            return {}

    def write_metadata(self, input_path: str, output_path: str, tags: dict) -> list:
        """
        Generates the FFmpeg command list to write metadata tags.
        Returns the command list to be executed by the TaskWorker.
        """
        # Map 0 (all streams) and copy codecs (lossless, instant)
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-map', '0',
            '-c', 'copy',
            '-ignore_unknown'
        ]

        # Add global metadata flags
        for key, val in tags.items():
            cmd.extend(['-metadata', f'{key}={val}'])

        cmd.append(output_path)
        return cmd
