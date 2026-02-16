"""
Local Fetcher - Multi-Sport Version with Dark Mode Support
Fetches data for all supported sports
"""

import requests
import json
import os
import subprocess
import glob
from datetime import datetime
from sports_config import PRIZEPICKS_LEAGUES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://app.prizepicks.com/"
}

def fetch_sport(sport_name, league_id):
    """Fetch data for a single sport"""
    print(f"\n{'='*60}")
    print(f"📊 Fetching {sport_name} (League ID: {league_id})...")
    print(f"{'='*60}")
    
    url = f"https://api.prizepicks.com/projections?league_id={league_id}&per_page=250"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch {sport_name} (Status: {response.status_code})")
            return None
            
        data = response.json()
        
        # Create lookup dictionaries
        players = {}
        teams = {}
        
        for item in data.get('included', []):
            item_type = item.get('type')
            attributes = item.get('attributes', {})
            
            if item_type == 'new_player':
                players[item['id']] = {
                    'name': attributes.get('name', 'Unknown'),
                    'team_id': attributes.get('team_id')
                }
            elif item_type == 'team':
                teams[item['id']] = attributes.get('name', 'Unknown')
        
        print(f"👥 Found {len(players)} players, {len(teams)} teams")
        
        # Parse props
        props = []
        stat_counts = {}
        
        for item in data.get('data', []):
            attrs = item.get('attributes', {})
            relationships = item.get('relationships', {})
            
            player_data = relationships.get('new_player', {}).get('data', {})
            player_id = player_data.get('id')
            player_info = players.get(player_id, {})
            player_name = player_info.get('name', 'Unknown')
            team_id = player_info.get('team_id')
            team_name = teams.get(team_id, 'Unknown')
            
            line_score = attrs.get('line_score')
            stat_type = attrs.get('stat_type', 'Unknown')
            start_time = attrs.get('start_time', '')
            
            # Track stat types
            if stat_type not in stat_counts:
                stat_counts[stat_type] = 0
            stat_counts[stat_type] += 1
            
            if player_name != 'Unknown' and line_score:
                try:
                    props.append({
                        'player': player_name,
                        'line': float(line_score),
                        'stat_type': stat_type,
                        'team': team_name,
                        'sport': sport_name,
                        'game_time': start_time,
                        'fetched_at': datetime.now().isoformat()
                    })
                except (ValueError, TypeError):
                    continue
        
        print(f"📊 Stat types found: {len(stat_counts)}")
        # Show top 5 stat types
        top_stats = sorted(stat_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for stat, count in top_stats:
            print(f"   • {stat}: {count} props")
        
        print(f"✅ Total props: {len(props)}")
        return props
        
    except requests.exceptions.Timeout:
        print("❌ Timeout error")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def save_to_json(props, sport_name):
    """Save props to JSON file"""
    if not props:
        return False
        
    # Sanitize sport name for filename
    sport_file = sport_name.lower().replace(' ', '_')
    filename = f"prizepicks_{sport_file}_latest.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(props, f, indent=2)
        
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"💾 Saved {len(props)} props to {filename} ({size} bytes)")
            return True
        else:
            print(f"❌ Failed to save {filename}")
            return False
            
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")
        return False

def push_to_github():
    """Push JSON files to GitHub"""
    print("\n📤 Pushing to GitHub...")
    
    try:
        json_files = glob.glob("prizepicks_*_latest.json")
        
        if not json_files:
            print("❌ No JSON files found to commit")
            return False
            
        print(f"Found files: {json_files}")
        
        for file in json_files:
            subprocess.run(["git", "add", file], check=True)
            print(f"  ✅ Added {file}")
        
        # Check if there are changes to commit
        result = subprocess.run(["git", "diff", "--staged", "--quiet"], capture_output=True)
        
        if result.returncode != 0:
            commit_msg = f"Auto-update PrizePicks data - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            subprocess.run(["git", "push"], check=True)
            print("✅ Successfully pushed to GitHub!")
            
            print("\n📊 Updated files:")
            for file in json_files:
                size = os.path.getsize(file)
                print(f"  - {file} ({size} bytes)")
        else:
            print("📭 No changes to commit")
            
        return True
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")
        return False

def main():
    """Main function - fetches all configured sports"""
    print("=" * 60)
    print("🎯 PrizePicks Multi-Sport Data Fetcher")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    print(f"📋 Active sports: {len(PRIZEPICKS_LEAGUES)}")
    
    all_props = {}
    successful_sports = []
    
    # Fetch each sport
    for sport_name, league_id in PRIZEPICKS_LEAGUES.items():
        props = fetch_sport(sport_name, league_id)
        
        if props and len(props) > 0:
            if save_to_json(props, sport_name):
                successful_sports.append(sport_name)
                all_props[sport_name] = props
                print(f"✅ {sport_name}: {len(props)} props")
        
        # Small delay between requests
        import time
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    
    total_props = 0
    for sport in successful_sports:
        count = len(all_props[sport])
        total_props += count
        print(f"✅ {sport}: {count} props")
    
    print(f"\n📈 Total: {total_props} props across {len(successful_sports)} sports")
    
    if successful_sports:
        print("\n" + "=" * 60)
        push_to_github()
    
    print("\n" + "=" * 60)
    print("✨ Multi-sport fetch complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()