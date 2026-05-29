# Onyx Engine Architecture Guide

Welcome to the internal architecture guide for the Onyx Engine. This document is designed for developers who wish to understand how the application is structured, how to navigate the codebase, and how to extend its functionality.

## Core Design Philosophy

Onyx Engine is built on a strict **separation of concerns**. It acts as a massive orchestration layer between a Python-based graphical user interface (PyQt6) and the underlying FFmpeg/FFprobe binaries. 

The application is never meant to process video in pure Python (which would be catastrophically slow). Instead, Python handles the logic, math, API calls, and string manipulation required to build complex FFmpeg shell commands, which are then passed to the OS to execute asynchronously.

---

## Codebase Directory Structure

```text
Onyx Engine/
│
├── main.py                   # The primary CLI entrypoint and bootstrapping script.
├── gui_main.py               # The primary GUI entrypoint. Bootstraps the PyQt6 application.
├── requirements.txt          # Python dependencies (PyQt6, requests, pyqtdarktheme, etc.)
│
├── src/                      # The core source code directory
│   │
│   ├── processors/           # THE BACKEND. Contains all business logic and FFmpeg orchestration.
│   │   ├── chronicle/        # Sub-module for TMDB API scraping and file logistics.
│   │   ├── editor.py         # Handles auto-shorts and division.
│   │   ├── timeline_composer.py # The massive NLE filter_complex generator.
│   │   └── [other processors]
│   │
│   ├── ui/                   # THE FRONTEND. Contains all PyQt6 visual components.
│   │   ├── dashboard_ui.py   # The main navigation hub.
│   │   ├── custom_widgets.py # Reusable Drag-and-Drop zones, Buttons, and VLC sliders.
│   │   ├── video_player.py   # PyQt6 QMediaPlayer wrappers for live previewing.
│   │   └── [other UIs]
│   │
│   └── utils/                # UTILITIES. Helper scripts.
│       ├── system.py         # Subprocess monkeys patching for global ETA calculation.
│       └── watcher.py        # File watchers and threading tools.
```

---

## 1. The Frontend Layer (`src/ui/`)

Every screen you see in the application (e.g., Timeline Composer, Scene Sniper, AI Restoration) is its own isolated class inheriting from `QWidget`.

*   **Navigation**: `gui_main.py` uses a `QStackedWidget` to hold instances of all these UI classes. Clicking a button on the sidebar simply changes the active index of the stacked widget.
*   **Custom Widgets**: To maintain a consistent dark-mode aesthetic, highly reused elements (like the dashed-border Drop Zones, the blue SmartRunButtons, and the green VLC-style volume sliders) are abstracted into `src/ui/custom_widgets.py`.
*   **Event Driven**: The UI is entirely event-driven. It listens for `clicked` signals on buttons, which then gather data from input fields and pass that data directly to the Backend Processors.

---

## 2. The Backend Layer (`src/processors/`)

This is where the magic happens. A processor file (like `timeline_composer.py` or `remaster.py`) does **not** know about the UI. It operates entirely independently.

*   **Stateless Execution**: Most processors are designed to be instantiated, run a specific method (like `convert_to_shorts_style`), and return a `True/False` boolean upon completion.
*   **Command Generation**: A processor's primary job is to build a `subprocess.Popen` array. For example, it translates user inputs into `-vf "scale=1920:1080,eq=brightness=0.5"` flags.
*   **Real-time Interception**: The `subprocess.Popen` execution is often intercepted globally (via `src/utils/system.py`) to parse FFmpeg's `stderr` output in real-time. This allows the backend to calculate completion percentage and emit those signals back to the UI's progress bars.

---

## 3. The Data Logistics Layer (`src/processors/chronicle/`)

Unlike the FFmpeg processors, the Chronicle module acts as a filesystem librarian.
*   **TMDB API**: Uses the `requests` library to fetch JSON metadata about TV shows.
*   **Regex Parsing**: Heavily utilizes Python's `re` module to guess season and episode numbers from messy torrent file names (e.g., `Show.Name.S01E02.1080p.mkv`).
*   **Filesystem Operations**: Uses `shutil` and `os` to construct beautiful, Plex-compliant directory trees (`/TV Shows/Show Name/Season 1/S01E01 - Title.mkv`).

---

## How to Add a New Feature

If you want to add a new tool (e.g., an Audio Normalizer):
1.  **Create the Backend**: Write `src/processors/normalizer.py`. It should take an input file path and output file path, and run the FFmpeg loudness normalization filter.
2.  **Create the Frontend**: Write `src/ui/normalizer_ui.py`. Design a simple interface with a DropZone and a SmartRunButton.
3.  **Connect them**: Inside `normalizer_ui.py`, when the run button is clicked, spawn a `QThread` that executes the logic from `src/processors/normalizer.py`.
4.  **Register it**: Add a button to `gui_main.py` that switches the `QStackedWidget` to your new UI!
