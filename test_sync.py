import sys
import threading
from src.ui.custom_widgets import TaskWorker
from src.processors.formats import FormatMapper
import subprocess

original = subprocess.run
def run(*args, **kwargs):
    if isinstance(threading.current_thread(), TaskWorker):
        return threading.current_thread().execute_subprocess_with_progress(args[0], **kwargs)
    return original(*args, **kwargs)
subprocess.run = run

mapper = FormatMapper()
input_path = "C:/Users/Hrushikesh Bunni/Downloads/Telegram Desktop/C/Passenger.57.1992.1080p.BluRay.H264.AAC-RARBG.mp4.mp4"
output_dir = "C:/Users/Hrushikesh Bunni/Downloads/Telegram Desktop/C/Onyx_Converted"
target_fmt = "mkv"

def my_task():
    success, errors = mapper.process_input(input_path, output_dir, target_fmt)
    return True, f"Format conversion finished. Success: {success} | Errors: {errors}"

worker = TaskWorker(my_task)

try:
    worker.run()
except Exception as e:
    import traceback
    traceback.print_exc()
