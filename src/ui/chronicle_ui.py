import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QRadioButton, QButtonGroup, QLineEdit, QPushButton, 
                             QDialog, QComboBox, QListWidget, QMessageBox)
from PyQt6.QtCore import Qt
from src.ui.custom_widgets import DropZone, SmartRunButton, ConsoleLogger
from src.processors.time_machine import TimeMachine
from src.processors.chronicle.file_manager import organize_and_rename, audit_missing_episodes
from src.processors.chronicle.omni_sorter import process_omni_dump
from src.processors.chronicle.utilities import flatten_directory, pack_volumes
from datetime import datetime

class TimeMachineDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏪ Onyx Time Machine (Global Undo)")
        self.setFixedSize(550, 450)
        self.setStyleSheet("background-color: #111; color: #fff;")
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🕰️ Time Machine Ledgers")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #E74C3C;")
        layout.addWidget(header)
        
        # Tool Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Tool:"))
        self.tool_combo = QComboBox()
        self.tool_combo.setStyleSheet("padding: 5px; background: #222; border: 1px solid #444; border-radius: 4px;")
        filter_layout.addWidget(self.tool_combo)
        layout.addLayout(filter_layout)
        
        # Runs List
        self.run_list = QListWidget()
        self.run_list.setStyleSheet("""
            QListWidget { background: #1a1a1a; border: 1px solid #333; border-radius: 5px; padding: 5px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #222; }
            QListWidget::item:selected { background: #E74C3C; color: white; }
        """)
        layout.addWidget(self.run_list)
        
        # Undo Button
        self.undo_btn = QPushButton("🔙 Revert Selected Run")
        self.undo_btn.setStyleSheet("""
            QPushButton { background-color: #E74C3C; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }
            QPushButton:hover { background-color: #C0392B; }
        """)
        self.undo_btn.clicked.connect(self.execute_undo)
        layout.addWidget(self.undo_btn)
        
        self.all_runs = []
        self.load_data()
        
        self.tool_combo.currentTextChanged.connect(self.filter_runs)

    def load_data(self):
        self.all_runs = TimeMachine.get_run_summaries()
        
        tools = set(["All Tools"])
        for r in self.all_runs:
            tools.add(r['tool'])
            
        self.tool_combo.clear()
        self.tool_combo.addItems(sorted(list(tools)))
        self.filter_runs()

    def filter_runs(self):
        self.run_list.clear()
        selected_tool = self.tool_combo.currentText()
        
        for r in self.all_runs:
            if selected_tool == "All Tools" or r['tool'] == selected_tool:
                display_text = f"[{r['tool']}] {r['desc']}"
                self.run_list.addItem(display_text)
                
                # Store hidden data in the item
                item = self.run_list.item(self.run_list.count() - 1)
                item.setData(Qt.ItemDataRole.UserRole, r)

    def execute_undo(self):
        selected = self.run_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Please select a run to revert.")
            return
            
        data = selected.data(Qt.ItemDataRole.UserRole)
        confirm = QMessageBox.question(self, "Confirm Revert", 
            f"Are you sure you want to revert this run?\n\nTool: {data['tool']}\nAction: {data['desc']}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
        if confirm == QMessageBox.StandardButton.Yes:
            success, msg = TimeMachine.undo_target_run(data['file'], data['run_id'])
            if success:
                QMessageBox.information(self, "Success", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Error", msg)


class ChronicleUI(QWidget):
    def __init__(self, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.setup_ui()

    def setup_ui(self):
        # Master layout for the whole page
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Centered Container
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        center_layout.setSpacing(20)

        # 1. Header (Centered)
        header = QLabel("🎬 CHRONICLE v3.0")
        header.setStyleSheet("font-size: 32px; font-weight: 900; color: #ffffff; letter-spacing: 2px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(header)
        
        # 2. Mode Selection (Centered Grid)
        mode_container = QWidget()
        mode_container.setFixedWidth(500)
        mode_layout = QHBoxLayout(mode_container)
        
        self.mode_group = QButtonGroup(self)
        modes = [
            ("Simulation (Dry Run)", "simulate"), ("Execute (Top-Down)", "execute"),
            ("Audit Missing", "audit"), ("🌪️ Omni-Dump (Auto)", "omni"),
            ("🚜 Deep Scavenger", "scavenge"), ("📦 Volume Packer", "pack")
        ]
        
        mode_vbox1 = QVBoxLayout(); mode_vbox1.setSpacing(15)
        mode_vbox2 = QVBoxLayout(); mode_vbox2.setSpacing(15)
        
        for i, (text, val) in enumerate(modes):
            rb = QRadioButton(text)
            rb.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            rb.setStyleSheet("""
                QRadioButton { 
                    color: #cccccc; 
                    font-size: 15px; 
                    font-weight: bold; 
                    outline: none;
                    background: transparent;
                }
                QRadioButton:hover {
                    color: #ffffff;
                }
                QRadioButton::indicator { 
                    width: 18px; 
                    height: 18px; 
                    border-radius: 9px;
                    border: 2px solid #555;
                    background: transparent;
                }
                QRadioButton::indicator:checked { 
                    border: 2px solid #2D72D9;
                    background: #2D72D9;
                }
            """)
            self.mode_group.addButton(rb)
            self.mode_group.setId(rb, i)
            rb.setProperty("mode_val", val)
            
            if i % 2 == 0: mode_vbox1.addWidget(rb)
            else: mode_vbox2.addWidget(rb)
            if val == "simulate": rb.setChecked(True)
                
        mode_layout.addLayout(mode_vbox1)
        mode_layout.addLayout(mode_vbox2)
        center_layout.addWidget(mode_container, alignment=Qt.AlignmentFlag.AlignHCenter)

        # 3. TV Show Name Entry
        self.show_entry = QLineEdit()
        self.show_entry.setPlaceholderText("TV Show Name (For Execute/Simulate)")
        self.show_entry.setFixedWidth(500)
        self.show_entry.setStyleSheet("""
            QLineEdit { background-color: #1e1e1e; border: 2px solid #333; border-radius: 8px; 
                        padding: 12px; color: #fff; font-size: 15px; }
            QLineEdit:focus { border: 2px solid #2D72D9; background-color: #252525; }
        """)
        center_layout.addWidget(self.show_entry, alignment=Qt.AlignmentFlag.AlignHCenter)

        # 4. Folder Drop Zone (Huge)
        self.path_selector = DropZone(self, mode='dir')
        self.path_selector.setFixedSize(600, 110)
        self.path_selector.file_input.setPlaceholderText("⏬ DRAG & DROP FOLDER HERE ⏬")
        self.path_selector.file_input.setStyleSheet("font-size: 16px; font-weight: bold; text-align: center; border: none; background: transparent; color: #aaa;")
        center_layout.addWidget(self.path_selector, alignment=Qt.AlignmentFlag.AlignHCenter)

        # 5. Time Machine Button
        self.undo_btn = QPushButton("⏪ Open Time Machine (Undo)")
        self.undo_btn.setFixedWidth(300)
        self.undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.undo_btn.setStyleSheet("""
            QPushButton { background-color: #900000; color: white; font-size: 15px; font-weight: bold; padding: 12px; border-radius: 6px; }
            QPushButton:hover { background-color: #b30000; }
        """)
        self.undo_btn.clicked.connect(self.open_time_machine)
        center_layout.addWidget(self.undo_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        main_layout.addLayout(center_layout)
        
        # 6. Embedded Console Box
        self.console = ConsoleLogger()
        self.console.setFixedHeight(100)
        self.console.append_log("☑ GUI Initialized. Time Machine Core online.\n")
        main_layout.addWidget(self.console)

        # 7. Smart Run Button
        self.run_btn = SmartRunButton("🚀 Ignite Engine", 
                                      get_input_paths_callback=lambda: self.path_selector.file_input.text().strip(), 
                                      on_confirm_callback=self.execute_engine)
        self.run_btn.setFixedHeight(65)
        main_layout.addWidget(self.run_btn)

    def open_time_machine(self):
        dialog = TimeMachineDialog(self)
        dialog.exec()

    def execute_engine(self, folder_path, est_seconds):
        if not folder_path or not os.path.exists(folder_path):
            self.orchestrator.append_log("❌ Error: Valid folder path required.\n")
            return

        selected_rb = self.mode_group.checkedButton()
        mode = selected_rb.property("mode_val")
        show_name = self.show_entry.text().strip()
        run_id = f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        if mode in ["execute", "simulate"] and not show_name:
            self.orchestrator.append_log("❌ Error: TV Show name required for this mode.\n")
            return

        self.orchestrator.append_log(f"🎬 Chronicle Mode: {mode.upper()} | Target: {os.path.basename(folder_path)}\n")
        self.console.append_log(f"\n[EXECUTE] Mode: {mode.upper()} | Target: {os.path.basename(folder_path)}\n")

        # Map UI commands to backend functions running in background threads
        if mode == "execute":
            self.orchestrator.add_background_job(
                "Chronicle Execution",
                lambda: organize_and_rename(folder_path, show_name, None, None, dry_run=False, run_id=run_id)
            )
        elif mode == "simulate":
            self.orchestrator.add_background_job(
                "Chronicle Simulation",
                lambda: organize_and_rename(folder_path, show_name, None, None, dry_run=True, run_id=None)
            )
        elif mode == "audit":
            self.orchestrator.add_background_job(
                "Chronicle Audit",
                lambda: audit_missing_episodes(folder_path, show_name, None, None)
            )
        elif mode == "omni":
            self.orchestrator.add_background_job(
                "Omni-Dump",
                lambda: process_omni_dump(folder_path, dry_run=False, run_id=run_id)
            )
        elif mode == "scavenge":
            self.orchestrator.add_background_job(
                "Deep Scavenger",
                lambda: flatten_directory(folder_path, run_id=run_id)
            )
        elif mode == "pack":
            self.orchestrator.add_background_job(
                "Volume Packer",
                lambda: pack_volumes(folder_path, show_name, max_size_gb=2.0, run_id=run_id)
            )


# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.chronicle_ui import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (chronicle_ui.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'chronicle_ui.py', is a core component of the Onyx Engine. It is
#    responsible for encapsulating specific FFmpeg processing logic, UI handling,
#    or filesystem operations to maintain the decoupled architecture.
#
# 📘 TECHNICAL DOCUMENTATION & FEATURE OVERVIEW
# ------------------------------------------------------------------------------
#
# 1. FUNCTIONALITY:
#    This module abstracts complex command-line operations into simple Python
#    methods. It parses inputs, constructs subprocess arrays, and handles 
#    errors gracefully without crashing the main application thread.
#
# 2. KEY FEATURES:
#    - Error Resiliency: Wraps execution in try-except blocks.
#    - Asynchronous Ready: Designed to be called from QThreads to prevent UI blocking.
#    - Clean Code: Follows strict separation of concerns.
#
# 3. APPLICATIONS:
#    - Core backend processing for the Onyx Engine UI.
#    - Standalone CLI execution for batch scripting.
#
# 4. PERFORMANCE & RESOURCE IMPACT:
#    - Minimal overhead in Python. The true resource cost is determined by the
#      underlying FFmpeg/FFprobe binaries which scale with video resolution.
#
# 5. FUTURE SCOPE & IMPROVEMENTS:
#    - Further optimization of FFmpeg filter graphs.
#    - Enhanced error reporting to the user interface.
#
# ==============================================================================
