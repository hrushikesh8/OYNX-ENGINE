import subprocess
import json

class TrackProcessor:
    def get_track_info(self, input_path: str, stream_type='a') -> list:
        """
        Returns a list of tracks with CODEC info to detect broken streams.
        """
        cmd = [
            'ffprobe', '-v', 'error',
            # We added 'codec_name' here to spot the 'none' codecs
            '-show_entries', 'stream=index,codec_name:stream_tags=language,title',
            '-select_streams', stream_type,
            '-of', 'json',
            input_path
        ]
        try:
            output = subprocess.check_output(cmd)
            data = json.loads(output)
            return data.get('streams', [])
        except Exception as e:
            print(f"Error reading tracks: {e}")
            return []

    def keep_multiple_tracks(self, input_path, output_path, track_indices, stream_type='a'):
        """
        Surgically maps only VALID streams. 
        explicitly skips any stream where codec_name is 'none' or 'unknown'.
        """
        # 1. Map the MAIN VIDEO only (usually the first video stream)
        # We use 0:v:0 to avoid accidentally grabbing cover art images as video
        cmd = ['ffmpeg', '-i', input_path, '-map', '0:v:0']

        # 2. Map the SELECTED tracks (Audio or Subtitle)
        # (The ones you chose by ID)
        for idx in track_indices:
            cmd.extend(['-map', f'0:{stream_type}:{idx}'])

        # 3. Smart-Map the UNTOUCHED tracks
        # If you selected Audio, we need to check the Subtitles for errors.
        other_type = 's' if stream_type == 'a' else 'a'
        
        # Get list of all tracks of the other type
        other_tracks = self.get_track_info(input_path, other_type)
        
        print(f"   🔍 Scanning {len(other_tracks)} {other_type.upper()} tracks for errors...")

        valid_count = 0
        for i, track in enumerate(other_tracks):
            codec = track.get('codec_name', 'unknown')
            
            # THE FIX: If codec is 'none', we DO NOT add it to the command.
            if codec == 'none' or codec == 'unknown':
                print(f"   ⚠️ Skipping BROKEN stream #{i} (Codec: {codec})")
                continue
            
            # If valid, map it explicitly by its index
            cmd.extend(['-map', f'0:{other_type}:{i}'])
            valid_count += 1

        print(f"   ✅ Keeping {valid_count} valid {other_type.upper()} tracks.")

        # 4. Final settings
        cmd.extend([
            '-c', 'copy',           # Copy mode (Fast)
            '-ignore_unknown',      # Extra safety
            '-y', output_path
        ])

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg Logic Error: {e.stderr.decode('utf-8')}")
            return False

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
#
# Syntax: python src/processors/tracks.py <VideoPath> <Mode> <TrackIDs>
#
# Mode: 'a' for Audio, 's' for Subtitles
# TrackIDs: The index numbers of tracks to KEEP (separated by comma)
#
# Example Command:
# python src/processors/tracks.py "C:\Movies\Avatar.mkv" "a" "0,2"
#
# (This keeps Audio Track 0 and 2, removes the rest)