import os
import subprocess
import requests
import json
import gzip
import re
from io import BytesIO
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool

class SubtitleSignals(QObject):
    search_finished = pyqtSignal(list)
    download_finished = pyqtSignal(str)
    merge_finished = pyqtSignal(str)
    extract_finished = pyqtSignal(str)
    error = pyqtSignal(str)

class DummyLanguage:
    def __init__(self, name):
        self.name = name

class DummySubtitle:
    def __init__(self, data):
        self.provider_name = "OpenSubtitles"
        lang_name = data.get("LanguageName", "Unknown")
        self.language = DummyLanguage(lang_name)
        self.score = data.get("Score", 0)
        self.filename = data.get("SubFileName", "")
        self.download_link = data.get("SubDownloadLink", "")
        self.id = data.get("IDSubtitle", "")
        self.downloads = int(data.get("SubDownloadsCnt", 0))
        self.trusted = int(data.get("SubFromTrusted", 0))

def parse_title_year(filename):
    name = os.path.splitext(os.path.basename(filename))[0]
    
    # Extract year if present
    year = ""
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', name)
    if year_match:
        year = year_match.group(1)
        # Remove year and anything after it for title
        name = name[:year_match.start()]
        
    # Remove tags and formatting
    tags = [
        r'\b1080p\b', r'\b720p\b', r'\b2160p\b', r'\b4k\b',
        r'\bbluray\b', r'\bweb-dl\b', r'\bwebrip\b', r'\bhdrip\b', r'\bbrrip\b',
        r'\bx264\b', r'\bx265\b', r'\bhevc\b', r'\baac\b', r'\bflac\b',
        r'\bhdr\b', r'\bdv\b', r'\batmos\b', r'\bdual\s*audio\b',
        r'\bYTS.*?\b', r'\bGalaxyRG\b', r'\bEVO\b', r'\bRARBG\b', r'\bPSA\b', r'\bQxR\b',
        r'\bweb\b', r'\bdl\b'
    ]
    name = re.sub(r'[\.\_\-]', ' ', name)
    for t in tags:
        name = re.sub(t, '', name, flags=re.IGNORECASE)
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    title = ' '.join(name.split())
    
    return title, year

class SearchWorker(QRunnable):
    def __init__(self, title, year, signals):
        super().__init__()
        self.title = title
        self.year = year
        self.signals = signals

    def run(self):
        try:
            query = self.title
            if self.year:
                query += f" {self.year}"
            
            # Use the old OpenSubtitles REST API for text search
            url = f"https://rest.opensubtitles.org/search/query-{requests.utils.quote(query)}"
            headers = {'User-Agent': 'TemporaryUserAgent'}
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and data:
                    subs = [DummySubtitle(item) for item in data]
                    # Sort by Trusted (1 or 0) descending, then by Downloads descending
                    subs.sort(key=lambda x: (x.trusted, x.downloads), reverse=True)
                    # Limit to top 15 results
                    subs = subs[:15]
                    self.signals.search_finished.emit(subs)
                else:
                    self.signals.search_finished.emit([])
            else:
                self.signals.error.emit(f"API Error {response.status_code}")
                
        except Exception as e:
            self.signals.error.emit(str(e))

class DownloadWorker(QRunnable):
    def __init__(self, subtitle, video_path, signals):
        super().__init__()
        self.subtitle = subtitle
        self.video_path = video_path
        self.signals = signals

    def run(self):
        try:
            headers = {'User-Agent': 'TemporaryUserAgent'}
            res = requests.get(self.subtitle.download_link, headers=headers, timeout=15)
            
            if res.status_code == 200:
                # Decompress GZIP
                srt_content = gzip.GzipFile(fileobj=BytesIO(res.content)).read()
                
                # Save SRT next to video file
                base_dir = os.path.dirname(self.video_path)
                safe_name = self.subtitle.filename if self.subtitle.filename else f"subtitle_{self.subtitle.id}.srt"
                
                srt_path = os.path.join(base_dir, safe_name)
                
                with open(srt_path, 'wb') as f:
                    f.write(srt_content)
                    
                self.signals.download_finished.emit(srt_path)
            else:
                self.signals.error.emit(f"Failed to download. Status: {res.status_code}")
                
        except Exception as e:
            self.signals.error.emit(str(e))

class ExtractWorker(QRunnable):
    def __init__(self, video_path, output_format, track_id, signals):
        super().__init__()
        self.video_path = video_path
        self.output_format = output_format
        self.track_id = track_id
        self.signals = signals

    def run(self):
        try:
            base_dir, filename = os.path.split(self.video_path)
            name, _ = os.path.splitext(filename)
            suffix = f"_SubTrack{self.track_id}" if self.track_id > 0 else ""
            output_path = os.path.join(base_dir, f"{name}{suffix}.{self.output_format}")
            
            cmd = [
                'ffmpeg', '-y', '-i', self.video_path,
                '-map', f'0:s:{self.track_id}',
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            self.signals.extract_finished.emit(output_path)
        except subprocess.CalledProcessError as e:
            self.signals.error.emit(f"FFmpeg error: {e.stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            self.signals.error.emit(str(e))

class SubtitleProcessor(QObject):
    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        self.signals = SubtitleSignals()

    def search_subtitles(self, title, year):
        worker = SearchWorker(title, year, self.signals)
        self.threadpool.start(worker)

    def download_subtitle(self, subtitle, video_path):
        worker = DownloadWorker(subtitle, video_path, self.signals)
        self.threadpool.start(worker)

    def extract_subtitle(self, video_path, output_format="srt", track_id=0):
        worker = ExtractWorker(video_path, output_format, track_id, self.signals)
        self.threadpool.start(worker)

    def merge_subtitle(self, video_path, subtitle_path, output_path):
        try:
            cmd = [
                'ffmpeg', '-y', '-i', video_path, '-i', subtitle_path,
                '-c', 'copy', '-c:s', 'mov_text', output_path
            ]
            ext = os.path.splitext(output_path)[1].lower()
            if ext == '.mkv':
                cmd[9] = 'srt'
                
            subprocess.run(cmd, check=True)
            self.signals.merge_finished.emit(output_path)
        except subprocess.CalledProcessError as e:
            self.signals.error.emit(f"FFmpeg error: {e}")
        except Exception as e:
            self.signals.error.emit(str(e))
