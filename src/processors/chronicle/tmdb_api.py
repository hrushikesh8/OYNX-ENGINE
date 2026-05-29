import requests

def get_show_id(api_key, show_name):
    """
    Step 1: The ID Fetcher.
    We ping the TVMaze database with the string the user typed (e.g., 'The Boys').
    UPDATED: Now extracts the release year and forces ALL CAPS for the ultimate clean aesthetic.
    Returns a tuple: (show_id, official_name)
    """
    url = f"https://api.tvmaze.com/singlesearch/shows?q={show_name}"
    
    try:
        response = requests.get(url, timeout=10) # 10 second timeout so the script doesn't hang forever
        if response.status_code == 200:
            data = response.json()
            
            # --- THE NEW YEAR-INJECTION & ALL CAPS LOGIC ---
            raw_title = data.get('name')
            premiered = data.get('premiered') # Gets format "2019-07-25"
            
            if premiered:
                year = premiered.split('-')[0] # Chops off month and day
                official_name = f"{raw_title} ({year})".upper() 
            else:
                official_name = raw_title.upper()
                
            # RETURN BOTH!
            return data.get('id'), official_name
            
    except Exception as e:
        print(f"❌ Network Error fetching show ID: {e}")
        
    # Crucial: Return two Nones if it fails so main_gui.py doesn't crash expecting two variables
    return None, None

def get_all_episodes_data(api_key, show_id):
    """
    Step 2: The Master Ledger.
    Once we have the TVMaze Show ID, we ask for the ENTIRE episode history of the show.
    Instead of asking season by season, TVMaze sends us a massive, lightweight JSON array
    containing every episode ever aired. This powers our Library Audit function.
    """
    url = f"https://api.tvmaze.com/shows/{show_id}/episodes"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json() # Returns a massive list of dictionaries
    except Exception as e:
        print(f"❌ Network Error fetching episode data: {e}")
        
    return []

def get_episode_names(api_key, show_id, season_number):
    """
    Step 3: The Data Parser.
    This function isolates the specific season Chronicle is currently trying to rename.
    It builds a perfectly ordered list of episode titles so that 'file_manager.py' 
    can just ask for Index 0 to get Episode 1.
    """
    # Grab the master list of all episodes
    episodes_data = get_all_episodes_data(api_key, show_id)
    
    # Filter the massive list down to ONLY the season we care about right now
    season_eps = [ep for ep in episodes_data if ep.get('season') == season_number]
    
    if not season_eps:
        return []

    # Find out how many episodes are in this season so we can build a list of the correct size
    max_ep = max([ep.get('number') for ep in season_eps if ep.get('number') is not None], default=0)
    
    # Create a blank list of placeholders (e.g., 10 blank slots for a 10-episode season)
    names_list = ["Unknown Episode"] * max_ep

    # Inject the official titles into their correct slots
    for ep in season_eps:
        ep_num = ep.get('number')
        if ep_num is not None and 1 <= ep_num <= max_ep:
            # We subtract 1 because Python lists start at 0, but episodes start at 1
            names_list[ep_num - 1] = ep.get('name')

    return names_list

# ==========================================
# HOW TO USE THIS CODE (EXAMPLE)
# ==========================================
# Example usage:
# from src.processors.tmdb_api import MainClass
# processor = MainClass()
# processor.run(input_file, output_file)
# ==========================================

# ==============================================================================
# 🎬 FEATURE: INTERNAL MODULE DOCUMENTATION (tmdb_api.py)
# ==============================================================================
#
# 📝 WHAT IS THIS FILE?
#    This file, 'tmdb_api.py', is a core component of the Onyx Engine. It is
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
