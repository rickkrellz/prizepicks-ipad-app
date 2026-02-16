"""
Local Fetcher - Runs on your computer to get real PrizePicks data
Includes team information
"""

import requests
import json
import os
import subprocess
import glob
from datetime import datetime

# Configuration
SPORTS = {
    "NBA": 7,
    "NFL": 2,
    "MLB": 1,
    "NHL": 5
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://app.prizepicks.com/"
}

def fetch_sport(sport_name, league_id):
    """Fetch data for a single sport"""
    print(f"\n📊 Fetching {sport_name}...")
    
    url = f"https://api.prizepicks.com/projections?league_id={league_id}&per_page=250"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        print(f"Status: {response.status_code}")
        
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
        
        print(f"Found {len(players)} players, {len(teams)} teams")
        
        # Parse props
        props = []
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
            
            if player_name != 'Unknown' and line_score:
                try:
                    props.append({
                        'player': player_name,
                        'line': float(line_score),
                        'stat_type': stat_type,
                        'team': team_name,
                        'sport': sport_name,
                        'fetched_at': datetime.now().isoformat()
                    })
                except:
                    continue
        
        print(f"✅ Found {len(props)} props for {sport_name}")
        return props
        
    except Exception as e:
        print(f"❌ Error fetching {sport_name}: {e}")
        return None

def save_to_json(props, sport_name):
    """Save props to JSON file"""
    if not props:
        return False
        
    filename = f"prizepicks_{sport_name.lower()}_latest.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(props, f, indent=2)
        
        # Verify file was created
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
        # Get list of JSON files
        json_files = glob.glob("prizepicks_*_latest.json")
        
        if not json_files:
            print("❌ No JSON files found to commit")
            return False
            
        print(f"Found files: {json_files}")
        
        # Add files individually
        for file in json_files:
            subprocess.run(["git", "add", file], check=True)
            print(f"  ✅ Added {file}")
        
        # Check if there are changes to commit
        result = subprocess.run(["git", "diff", "--staged", "--quiet"], capture_output=True)
        
        if result.returncode != 0:  # There are changes
            commit_msg = f"Auto-update PrizePicks data - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            subprocess.run(["git", "push"], check=True)
            print("✅ Successfully pushed to GitHub!")
            
            # Show the push result
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
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_git_connection():
    """Test if git is working"""
    try:
        # Check git status
        result = subprocess.run(["git", "status"], capture_output=True, text=True)
        print(f"📁 Git status: {result.stdout[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Git not working: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("🎯 PrizePicks Local Data Fetcher (with Teams)")
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    
    # Test git connection
    test_git_connection()
    
    all_props = {}
    successful_sports = []
    
    # Fetch each sport
    for sport_name, league_id in SPORTS.items():
        props = fetch_sport(sport_name, league_id)
        
        if props:
            if save_to_json(props, sport_name):
                successful_sports.append(sport_name)
                all_props[sport_name] = props
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    for sport in successful_sports:
        print(f"✅ {sport}: {len(all_props[sport])} props")
    
    # Push to GitHub
    if successful_sports:
        print("\n" + "=" * 60)
        push_to_github()
    else:
        print("\n❌ No data fetched for any sport")
    
    print("\n" + "=" * 60)
    print("✅ Done!")

if __name__ == "__main__":
    main()
