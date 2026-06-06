import os
import sys
import threading
from PyQt6.QtWidgets import QApplication
from src.ui.custom_widgets import TaskWorker
from src.processors.formats import FormatMapper
import subprocess

app = QApplication(sys.argv)
mapper = FormatMapper()
input_path = "C:/Users/Hrushikesh Bunni/Downloads/Telegram Desktop/C/Passenger.57.1992.1080p.BluRay.H264.AAC-RARBG.mp4.mp4"
output_dir = "C:/Users/Hrushikesh Bunni/Downloads/Telegram Desktop/C/Onyx_Converted"
target_fmt = "mkv"

with open("debug_log.txt", "w", encoding="utf-8") as f:
    f.write("Started test script\n")

def my_task():
    try:
        success, errors = mapper.process_input(input_path, output_dir, target_fmt)
        return True, f"Success: {success} | Errors: {errors}"
    except Exception as e:
        import traceback
        with open("debug_log.txt", "a", encoding="utf-8") as f:
            f.write("EXCEPTION IN TASK:\n")
            f.write(traceback.format_exc() + "\n")
        raise e

worker = TaskWorker(my_task)

def on_finished(success, msg):
    with open("debug_log.txt", "a", encoding="utf-8") as f:
        f.write(f"FINISHED! success={success} msg={msg}\n")
    app.quit()
worker.finished_signal.connect(on_finished)

def on_log(msg):
    with open("debug_log.txt", "a", encoding="utf-8") as f:
        f.write(f"LOG: {msg}")
worker.log_signal.connect(on_log)

worker.start()
app.exec()
