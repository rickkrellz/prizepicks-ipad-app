# scheduler.py
import schedule
import time
import logging
from datetime import datetime
from prizepicks_scraper import get_daily_props
import pandas as pd
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrizePicksScheduler:
    def __init__(self):
        self.data_dir = "daily_data"
        os.makedirs(self.data_dir, exist_ok=True)
        
    def update_all_sports(self):
        """Update data for all major sports"""
        sports = ["NBA", "NFL", "MLB", "NHL"]
        
        for sport in sports:
            try:
                logger.info(f"Updating {sport} data...")
                df = get_daily_props(sport=sport, headless=True)
                
                if not df.empty:
                    date_str = datetime.now().strftime('%Y%m%d')
                    filename = f"{sport.lower()}_{date_str}.csv"
                    filepath = os.path.join(self.data_dir, filename)
                    df.to_csv(filepath, index=False)
                    
                    # Save latest copy for app
                    latest_file = os.path.join(self.data_dir, f"{sport.lower()}_latest.csv")
                    df.to_csv(latest_file, index=False)
                    
                    logger.info(f"✓ Updated {sport}: {len(df)} props")
                else:
                    logger.warning(f"✗ No data for {sport}")
                    
            except Exception as e:
                logger.error(f"Error updating {sport}: {e}")
        
        self.create_combined_file()
    
    def create_combined_file(self):
        """Combine all latest data"""
        all_dfs = []
        for sport in ["NBA", "NFL", "MLB", "NHL"]:
            latest_file = os.path.join(self.data_dir, f"{sport.lower()}_latest.csv")
            if os.path.exists(latest_file):
                df = pd.read_csv(latest_file)
                df['sport'] = sport
                all_dfs.append(df)
        
        if all_dfs:
            combined = pd.concat(all_dfs, ignore_index=True)
            combined.to_csv(os.path.join(self.data_dir, "all_sports_latest.csv"), index=False)

if __name__ == "__main__":
    scheduler = PrizePicksScheduler()
    # Run once immediately
    scheduler.update_all_sports()
    
    # Schedule daily updates
    schedule.every().day.at("08:00").do(scheduler.update_all_sports)
    schedule.every().day.at("12:00").do(scheduler.update_all_sports)
    schedule.every().day.at("16:00").do(scheduler.update_all_sports)
    schedule.every().day.at("20:00").do(scheduler.update_all_sports)
    
    logger.info("Scheduler started. Running forever...")
    while True:
        schedule.run_pending()
        time.sleep(60)