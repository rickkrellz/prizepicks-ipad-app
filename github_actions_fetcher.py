"""
GitHub Actions Fetcher - Runs in the cloud to fetch PrizePicks data
With detailed error logging
"""

import requests
import pandas as pd
import json
from datetime import datetime
import sys
import traceback

def fetch_prizepicks_data(sport="NBA"):
    """Fetch real PrizePicks data"""
    print(f"\n🔍 Starting fetch for {sport}...")
    
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
        print(f"📡 Requesting URL: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Got successful response, parsing data...")
            data = response.json()
            
            # Parse data
            players = {}
            print(f"📦 Processing included data...")
            
            for item in data.get('included', []):
                if item.get('type') == 'new_player':
                    players[item['id']] = item['attributes']['name']
            
            print(f"👥 Found {len(players)} players")
            
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
            
            print(f"✅ Successfully parsed {len(props)} props for {sport}")
            return pd.DataFrame(props)
        else:
            print(f"❌ API returned {response.status_code} for {sport}")
            print(f"Response text: {response.text[:200]}")  # First 200 chars
            return None
    except requests.exceptions.Timeout:
        print(f"❌ Timeout error for {sport}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error for {sport}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error for {sport}: {e}")
        traceback.print_exc()
        return None

def update_all_sports():
    """Update data for all sports"""
    print("🎯 PrizePicks GitHub Actions Fetcher")
    print("=" * 40)
    print(f"📅 Time: {datetime.now().isoformat()}")
    
    sports = ["NBA", "NFL", "MLB", "NHL"]
    success_count = 0
    
    for sport in sports:
        print(f"\n{'='*40}")
        print(f"📊 Processing {sport}...")
        print(f"{'='*40}")
        
        df = fetch_prizepicks_data(sport)
        
        if df is not None and not df.empty:
            filename = f"prizepicks_{sport.lower()}_latest.json"
            
            # Save as JSON
            with open(filename, 'w') as f:
                json.dump(df.to_dict('records'), f, indent=2)
            
            print(f"✅ Saved {len(df)} {sport} props to {filename}")
            
            # Verify file was created
            import os
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"📁 File size: {file_size} bytes")
                success_count += 1
            else:
                print(f"❌ File was not created!")
        else:
            print(f"❌ Failed to fetch {sport}")
    
    print(f"\n{'='*40}")
    print(f"✨ Done! Updated {success_count}/{len(sports)} sports")
    
    if success_count == 0:
        print("❌ No data fetched for any sport! Exiting with error.")
        sys.exit(1)
    else:
        print("✅ Partial success - some sports updated")

if __name__ == "__main__":
    try:
        update_all_sports()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
