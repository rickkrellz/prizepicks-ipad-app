"""
GitHub Actions Fetcher - Runs in the cloud to fetch PrizePicks data
"""

import requests
import pandas as pd
import json
from datetime import datetime
import sys

def fetch_prizepicks_data(sport="NBA"):
    """Fetch real PrizePicks data"""
    league_ids = {
        "NBA": 7,
        "NFL": 2,
        "MLB": 1,
        "NHL": 5,
    }
    
    league_id = league_ids.get(sport, 7)
    url = f"https://api.prizepicks.com/projections?league_id={league_id}&per_page=250&single_stat=true"
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://app.prizepicks.com",
        "Referer": "https://app.prizepicks.com/",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse data
            players = {}
            
            for item in data.get('included', []):
                if item.get('type') == 'new_player':
                    players[item['id']] = item['attributes']['name']
            
            props = []
            for item in data.get('data', []):
                attrs = item.get('attributes', {})
                rels = item.get('relationships', {})
                
                player_id = rels.get('new_player', {}).get('data', {}).get('id')
                player_name = players.get(player_id, 'Unknown')
                line_score = attrs.get('line_score')
                
                if player_name != 'Unknown' and line_score:
                    props.append({
                        'player': player_name,
                        'line': float(line_score),
                        'stat_type': attrs.get('stat_type', 'Unknown'),
                        'team': 'Unknown',
                        'sport': sport,
                        'timestamp': datetime.now().isoformat()
                    })
            
            print(f"✅ Fetched {len(props)} {sport} props")
            return pd.DataFrame(props)
        else:
            print(f"❌ API returned {response.status_code} for {sport}")
            return None
    except Exception as e:
        print(f"❌ Error fetching {sport}: {e}")
        return None

def update_all_sports():
    """Update data for all sports"""
    sports = ["NBA", "NFL", "MLB", "NHL"]
    success_count = 0
    
    for sport in sports:
        print(f"\n📊 Fetching {sport}...")
        df = fetch_prizepicks_data(sport)
        
        if df is not None and not df.empty:
            filename = f"prizepicks_{sport.lower()}_latest.json"
            df.to_json(filename, orient='records', indent=2)
            print(f"✅ Saved {len(df)} {sport} props to {filename}")
            success_count += 1
        else:
            print(f"❌ Failed to fetch {sport}")
    
    print(f"\n✨ Done! Updated {success_count}/{len(sports)} sports")
    
    # Exit with error if no sports succeeded
    if success_count == 0:
        sys.exit(1)

if __name__ == "__main__":
    print("🎯 PrizePicks GitHub Actions Fetcher")
    print("=" * 40)
    update_all_sports()
