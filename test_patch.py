import threading
from src.ui.custom_widgets import TaskWorker
import subprocess

original = subprocess.run
def run(*args, **kwargs):
    if isinstance(threading.current_thread(), TaskWorker):
        return threading.current_thread().execute_subprocess_with_progress(*args, **kwargs)
    return original(*args, **kwargs)
subprocess.run = run

worker = TaskWorker(['ffmpeg', '-version'])
try:
    worker.run()
except Exception as e:
    import traceback
    traceback.print_exc()
