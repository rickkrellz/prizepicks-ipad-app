"""
GitHub Actions Fetcher - With Authenticated Proxy Support
"""

import requests
import json
from datetime import datetime
import os
import random
import time
from requests.auth import HTTPProxyAuth

# Your authenticated proxies (IP:PORT:USER:PASS)
PROXY_LIST = [
    {"ip": "23.95.150.145", "port": "6114", "user": "yyhldrup", "pass": "2ozn2s0grww5"},
    {"ip": "198.23.239.134", "port": "6540", "user": "yyhldrup", "pass": "2ozn2s0grww5"},
    {"ip": "107.172.163.27", "port": "6543", "user": "yyhldrup", "pass": "2ozn2s0grww5"},
    {"ip": "216.10.27.159", "port": "6837", "user": "yyhldrup", "pass": "2ozn2s0grww5"},
    {"ip": "23.26.71.145", "port": "5628", "user": "yyhldrup", "pass": "2ozn2s0grww5"},
    {"ip": "23.229.19.94", "port": "8689", "user": "yyhldrup", "pass": "2ozn2s0grww5"},
]

def get_proxy_config():
    """Get a random proxy configuration"""
    proxy = random.choice(PROXY_LIST)
    
    proxy_url = f"http://{proxy['ip']}:{proxy['port']}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    auth = HTTPProxyAuth(proxy['user'], proxy['pass'])
    
    return proxies, auth

def fetch_with_retry(url, headers, max_retries=3):
    """Fetch with retry logic and proxy rotation"""
    
    for attempt in range(max_retries):
        proxies, auth = get_proxy_config()
        
        print(f"Attempt {attempt + 1}/{max_retries} - Using proxy: {proxies['http']}")
        
        try:
            response = requests.get(
                url, 
                headers=headers, 
                proxies=proxies,
                auth=auth,
                timeout=15
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Success with proxy {proxies['http']}")
                return response
            elif response.status_code in [403, 429]:
                print(f"⚠️ Proxy blocked (status {response.status_code}), trying next...")
                time.sleep(1)
            else:
                print(f"⚠️ Unexpected status {response.status_code}, trying next...")
                time.sleep(1)
                
        except Exception as e:
            print(f"❌ Error with proxy {proxies['http']}: {e}")
            time.sleep(1)
    
    print(f"❌ All proxies failed after {max_retries} attempts")
    return None

def fetch_and_save():
    """Fetch data and save to JSON files"""
    
    # Sports to fetch
    sports = [
        {"name": "NBA", "league_id": 7},
        {"name": "NFL", "league_id": 2},
        {"name": "MLB", "league_id": 1},
        {"name": "NHL", "league_id": 5},
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://app.prizepicks.com/",
        "Origin": "https://app.prizepicks.com"
    }
    
    print("🎯 PrizePicks Data Fetcher with Authenticated Proxies")
    print("=" * 60)
    print(f"📅 Time: {datetime.now()}")
    print(f"🔄 Loaded {len(PROXY_LIST)} proxies")
    print("=" * 60)
    
    files_created = []
    
    for sport in sports:
        print(f"\n{'='*60}")
        print(f"📊 Fetching {sport['name']}...")
        print(f"URL: https://api.prizepicks.com/projections?league_id={sport['league_id']}&per_page=250")
        
        url = f"https://api.prizepicks.com/projections?league_id={sport['league_id']}&per_page=250"
        
        response = fetch_with_retry(url, headers)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                
                # Parse player names
                players = {}
                for item in data.get('included', []):
                    if item.get('type') == 'new_player':
                        players[item['id']] = item['attributes']['name']
                
                print(f"👥 Found {len(players)} players")
                
                # Parse props
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
                            'sport': sport['name']
                        })
                
                print(f"📊 Found {len(props)} props")
                
                # Save to JSON file
                filename = f"prizepicks_{sport['name'].lower()}_latest.json"
                with open(filename, 'w') as f:
                    json.dump(props, f, indent=2)
                print(f"✅ Saved to {filename}")
                
                # Verify file exists
                if os.path.exists(filename):
                    size = os.path.getsize(filename)
                    print(f"📁 File size: {size} bytes")
                    files_created.append(filename)
                else:
                    print(f"❌ File not created!")
                    
            except Exception as e:
                print(f"❌ Error parsing data: {e}")
        else:
            status = response.status_code if response else "No response"
            print(f"❌ Failed to fetch {sport['name']} - Status: {status}")
    
    print(f"\n{'='*60}")
    print(f"✅ Fetch complete! Created {len(files_created)} files:")
    for f in files_created:
        print(f"  - {f}")
    
    # List all JSON files
    import glob
    json_files = glob.glob("*.json")
    print(f"\n📁 All JSON files: {json_files}")
    
    # Create a summary file
    with open('fetch_summary.txt', 'w') as f:
        f.write(f"Fetch completed: {datetime.now()}\n")
        f.write(f"Files created: {files_created}\n")

if __name__ == "__main__":
    fetch_and_save()
