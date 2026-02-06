import shutil

class SystemUtils:
    @staticmethod
    def check_ffmpeg_availability() -> bool:
        """Verifies if FFmpeg is installed and accessible.and returns True if it is, otherwise False."""
        return shutil.which("ffmpeg") is not None