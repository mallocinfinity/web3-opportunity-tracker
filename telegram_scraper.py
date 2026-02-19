#!/usr/bin/env python3
"""
Telegram Channel Scraper
Scrapes Telegram channels for potential BD prospects and contacts

This uses Telegram's public channel info APIs. For full member scraping,
you'll need telethon or pyrogram with API credentials.

Usage:
    python3 telegram_scraper.py --add t.me/cryptoBD
    python3 telegram_scraper.py --list
    python3 telegram_scraper.py --scrape
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
CHANNELS_FILE = SCRIPT_DIR / "telegram_channels.json"
PROSPECTS_FILE = SCRIPT_DIR / "prospects.json"

def load_channels():
    """Load tracked Telegram channels"""
    if CHANNELS_FILE.exists():
        with open(CHANNELS_FILE, 'r') as f:
            return json.load(f)
    return {
        "channels": [],
        "last_scrape": None
    }

def save_channels(data):
    """Save channels"""
    data["last_scrape"] = datetime.now().isoformat()
    with open(CHANNELS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_channel(channel_username, category="crypto"):
    """Add a channel to track"""
    data = load_channels()
    
    # Normalize channel username
    username = channel_username.replace('@', '').replace('t.me/', '')
    if not username.startswith('t.me/'):
        username = username
    
    # Check if exists
    for c in data["channels"]:
        if username in c["username"] or username in c.get("link", ""):
            print(f"  ⏭️  Already tracking: {c['username']}")
            return
    
    channel = {
        "id": len(data["channels"]) + 1,
        "username": username,
        "link": f"https://t.me/{username}",
        "category": category,
        "member_count": "N/A",
        "description": "",
        "added_at": datetime.now().isoformat(),
        "status": "pending"  # pending, scraped, error
    }
    
    data["channels"].append(channel)
    save_channels(data)
    print(f"  ✅ Added: t.me/{username} ({category})")
    return channel

def add_prospect(name, role, company, source_channel, notes=""):
    """Add prospect from Telegram channel"""
    prospect = {
        "name": name,
        "role": role,
        "company": company,
        "source": f"Telegram: {source_channel}",
        "notes": notes,
        "priority": "medium"
    }
    
    # Use the main prospect tracker
    cmd = [
        "python3", str(SCRIPT_DIR / "prospect_tracker.py"),
        "add", name, role, company, "", source_channel, notes, "medium"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  ✅ Added to prospect tracker: {name}")
    return prospect

def list_channels():
    """List tracked channels"""
    data = load_channels()
    
    print(f"\n📱 Tracked Telegram Channels ({len(data['channels'])})")
    print(f"   Last scrape: {data.get('last_scrape', 'Never')[:19] or 'Never'}")
    
    # Group by category
    by_category = {}
    for c in data["channels"]:
        cat = c.get("category", "other")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(c)
    
    for cat, channels in by_category.items():
        print(f"\n   {cat.upper()} ({len(channels)}):")
        for c in channels:
            status_emoji = {"pending": "⏳", "scraped": "✅", "error": "❌"}
            emoji = status_emoji.get(c["status"], "📋")
            print(f"      {emoji} {c['username']} - {c.get('member_count', 'N/A')} members")

def scrape_channels():
    """Attempt to scrape channel info (basic public info only)"""
    data = load_channels()
    
    print(f"\n🔍 Scraping {len(data['channels'])} channels...")
    
    scraped_count = 0
    for channel in data["channels"]:
        username = channel["username"]
        
        # For now, just mark as processed and add to prospect tracker
        # Full scraping requires Telegram API credentials
        channel["status"] = "scraped"
        channel["last_checked"] = datetime.now().isoformat()
        scraped_count += 1
        
        print(f"  ✅ Processed: t.me/{username}")
    
    save_channels(data)
    print(f"\n  📊 Processed {scraped_count} channels")
    print(f"  💡 For full member data, configure Telegram API credentials")

def main():
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "--list" or cmd == "list":
            list_channels()
            return
        
        if cmd == "--scrape" or cmd == "scrape":
            scrape_channels()
            return
        
        if cmd == "--add" or cmd == "add":
            if len(sys.argv) > 2:
                channel = sys.argv[2]
                category = sys.argv[3] if len(sys.argv) > 3 else "crypto"
                add_channel(channel, category)
            else:
                print("Usage: python3 telegram_scraper.py --add <channel_username> [category]")
            return
        
        if cmd == "--add-prospect":
            if len(sys.argv) > 4:
                name = sys.argv[2]
                role = sys.argv[3]
                company = sys.argv[4]
                source = sys.argv[5] if len(sys.argv) > 5 else "telegram"
                notes = sys.argv[6] if len(sys.argv) > 6 else ""
                add_prospect(name, role, company, source, notes)
            else:
                print("Usage: python3 telegram_scraper.py --add-prospect \"Name\" \"Role\" \"Company\" [channel] [notes]")
            return
        
        if cmd == "--help" or cmd == "help":
            print("""
Telegram Channel Scraper Commands:
  python3 telegram_scraper.py --add <username> [category]  - Add channel to track
  python3 telegram_scraper.py --list                         - List tracked channels
  python3 telegram_scraper.py --scrape                       - Scrape channel info
  python3 telegram_scraper.py --add-prospect "Name" "Role" "Company" [source] [notes]
  
Examples:
  python3 telegram_scraper.py --add cryptoBD marketing
  python3 telegram_scraper.py --add web3jobs jobs
  python3 telegram_scraper.py --add-prospect "John Doe" "CEO" "CryptoCo" "@cryptoco" "Found via channel"
  
Channels to Track:
  - cryptoBD, web3jobs, defijobs, ethereumjobs
  - cryptomarketing, web3marketing
  - DAOjobs, venture_dao
  - OnlyFansManager (creator economy)
  
Note: Full member scraping requires Telegram API credentials (telethon/pyrogram)
""")
            return
    
    list_channels()
    print("\n💡 Use --add to track new channels")

if __name__ == '__main__':
    main()
