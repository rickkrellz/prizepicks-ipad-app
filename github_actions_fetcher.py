"""
GitHub Actions Fetcher - Working version with debug logging
"""

import requests
import json
from datetime import datetime
import sys
import os

def log_message(msg):
    """Print message and also write to debug log"""
    print(msg)
    with open('fetcher_debug.log', 'a') as f:
        f.write(f"{datetime.now()}: {msg}\n")

def fetch_prizepicks_data(sport="NBA"):
    """Fetch real PrizePicks data"""
    league_ids = {
        "NBA": 7,
        "NFL": 2,
        "MLB": 1,
        "NHL": 5,
    }
    
    league_id = league_ids.get(sport, 7)
    url = f"https://api.prizepicks.com/projections?league_id={league_id}&per_page=250"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://app.prizepicks.com/",
        "Origin": "https://app.prizepicks.com"
    }
    
    try:
        log_message(f"Fetching {sport} from {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        log_message(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            log_message(f"Error: {response.status_code}")
            return None
            
        data = response.json()
        log_message(f"Got response data")
        
        # Create player lookup
        players = {}
        for item in data.get('included', []):
            if item.get('type') == 'new_player':
                players[item['id']] = item['attributes']['name']
        
        log_message(f"Found {len(players)} players")
        
        # Parse props
        props = []
        for item in data.get('data', []):
            attrs = item.get('attributes', {})
            rels = item.get('relationships', {})
            
            player_id = rels.get('new_player', {}).get('data', {}).get('id')
            player_name = players.get(player_id, 'Unknown')
            line_score = attrs.get('line_score')
            stat_type = attrs.get('stat_type', 'Unknown')
            
            if player_name != 'Unknown' and line_score:
                props.append({
                    'player': player_name,
                    'line': float(line_score),
                    'stat_type': stat_type,
                    'sport': sport
                })
        
        log_message(f"Found {len(props)} props for {sport}")
        return props
        
    except Exception as e:
        log_message(f"Error: {e}")
        return None

def save_data():
    """Save data for all sports"""
    log_message("="*50)
    log_message("Starting PrizePicks data fetch")
    
    sports = ["NBA", "NFL", "MLB", "NHL"]
    files_created = []
    
    for sport in sports:
        log_message(f"\n--- {sport} ---")
        props = fetch_prizepicks_data(sport)
        
        if props and len(props) > 0:
            filename = f"prizepicks_{sport.lower()}_latest.json"
            with open(filename, 'w') as f:
                json.dump(props, f, indent=2)
            log_message(f"✅ Saved {len(props)} props to {filename}")
            files_created.append(filename)
            
            # Verify file was created
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                log_message(f"📁 File size: {size} bytes")
            else:
                log_message(f"❌ File not found after saving!")
        else:
            log_message(f"❌ Failed to fetch {sport}")
    
    log_message(f"\n✅ Created files: {files_created}")
    
    # Write final summary
    with open('fetch_summary.txt', 'w') as f:
        f.write(f"Files created: {files_created}\n")
        f.write(f"Time: {datetime.now()}\n")

if __name__ == "__main__":
    print("🎯 PrizePicks Data Fetcher with Debug")
    print("=" * 40)
    save_data()
    print("\n✅ Done! Check fetcher_debug.log for details")
