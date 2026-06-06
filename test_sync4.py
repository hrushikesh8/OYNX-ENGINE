import sys
import threading
from PyQt6.QtWidgets import QApplication
from src.ui.custom_widgets import TaskWorker
from src.processors.formats import FormatMapper

app = QApplication(sys.argv)
mapper = FormatMapper()
input_path = "C:/Users/Hrushikesh Bunni/Downloads/Telegram Desktop/C/Passenger.57.1992.1080p.BluRay.H264.AAC-RARBG.mp4.mp4"
output_dir = "C:/Users/Hrushikesh Bunni/Downloads/Telegram Desktop/C/Onyx_Converted"
target_fmt = "mkv"

def my_task():
    success, errors = mapper.process_input(input_path, output_dir, target_fmt)
    return True, f"Format conversion finished. Success: {success} | Errors: {errors}"

worker = TaskWorker(my_task)
orig_out = sys.stdout

def on_finished(success, msg):
    orig_out.write(f"FINISH -> success={success}, msg={msg}\n")
    orig_out.flush()
    app.quit()
worker.finished_signal.connect(on_finished)

def on_log(msg):
    orig_out.write(f"LOG -> {msg.strip()}\n")
    orig_out.flush()
worker.log_signal.connect(on_log)

worker.start()
app.exec()
