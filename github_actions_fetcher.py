"""
GitHub Actions Fetcher - Working version
"""

import requests
import json
from datetime import datetime
import sys
import os

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
        print(f"Fetching {sport}...")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return None
            
        data = response.json()
        
        # Create player lookup
        players = {}
        for item in data.get('included', []):
            if item.get('type') == 'new_player':
                players[item['id']] = item['attributes']['name']
        
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
        
        print(f"Found {len(props)} props for {sport}")
        return props
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def save_data():
    """Save data for all sports"""
    sports = ["NBA", "NFL", "MLB", "NHL"]
    
    for sport in sports:
        print(f"\n--- {sport} ---")
        props = fetch_prizepicks_data(sport)
        
        if props:
            filename = f"prizepicks_{sport.lower()}_latest.json"
            with open(filename, 'w') as f:
                json.dump(props, f, indent=2)
            print(f"✅ Saved {len(props)} props to {filename}")
        else:
            print(f"❌ Failed to fetch {sport}")

if __name__ == "__main__":
    print("🎯 PrizePicks Data Fetcher")
    print("=" * 40)
    save_data()
    print("\n✅ Done!")
