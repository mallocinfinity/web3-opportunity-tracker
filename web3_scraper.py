#!/usr/bin/env python3
"""
Web3 Opportunity Scraper
Scrapes Twitter and web for hackathons, Web3 jobs, and submission opportunities

This script generates queries for Evan to search. The actual search is done
via the agent's web_search tool for best results.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
SUBMISSIONS_FILE = SCRIPT_DIR / "submissions.json"
TASK_TRACKER = SCRIPT_DIR / "task_tracker.py"

def load_submissions():
    """Load existing submissions from JSON"""
    if SUBMISSIONS_FILE.exists():
        with open(SUBMISSIONS_FILE, 'r') as f:
            return json.load(f)
    return {
        "last_check": None,
        "opportunities": [],
        "submitted": []
    }

def save_submissions(data):
    """Save submissions to JSON"""
    with open(SUBMISSIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_task(title, description, priority="medium"):
    """Add a task to the tracker"""
    cmd = [
        "python3", str(TASK_TRACKER), "add",
        title, description, "--priority", priority
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()

def is_duplicate(opp):
    """Check if opportunity already tracked"""
    data = load_submissions()
    for existing in data.get("submitted", []):
        if existing.get("url") == opp.get("url"):
            return True
    return False

def log_opportunity(opp):
    """Log opportunity and create task"""
    data = load_submissions()
    
    # Check for duplicates
    if is_duplicate(opp):
        print(f"  ⏭️  Skipping duplicate: {opp['title'][:40]}...")
        return
    
    data["opportunities"].append(opp)
    save_submissions(data)
    
    print(f"  ✅ Found: {opp['title'][:50]}...")
    
    # Create task for this opportunity
    task_result = add_task(
        f"Apply: {opp['title'][:50]}",
        f"{opp.get('description', '')[:100]}... Source: {opp.get('source', 'unknown')}",
        opp.get("priority", "medium")
    )

def add_manual_opportunity(title, description, url, source="manual", priority="medium"):
    """Add an opportunity manually (from agent's web search)"""
    opp = {
        "title": title,
        "description": description[:200],
        "url": url,
        "source": source,
        "date": datetime.now().isoformat(),
        "priority": priority
    }
    log_opportunity(opp)

def run_search():
    """Main search function - generates queries for agent to search"""
    data = load_submissions()
    data["last_check"] = datetime.now().isoformat()
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Web3 Opportunity Scanner")
    print(f"  Last check: {data.get('last_check', 'Never')}")
    print(f"  Tracked: {len(data.get('opportunities', []))}")
    print(f"  Submitted: {len(data.get('submitted', []))}")
    
    # Search queries to run
    queries = [
        "web3 hackathon 2025 submission deadline",
        "ethereum grant program 2025 apply",
        "defi developer job remote hiring",
        "blockchain bounty program crypto",
        "DAO contributor program Web3",
        "l1 l2 ecosystem grants 2025",
        "nft project developer hiring",
        "gitcoin hackathon round",
    ]
    
    print(f"\n📋 Queries to search:")
    for i, q in enumerate(queries, 1):
        print(f"  {i}. {q}")
    
    print(f"\n💡 Tip: Run these searches and add opportunities with:")
    print(f"   python3 web3_scraper.py add \"Title\" \"Description\" https://url.com source")
    
    save_submissions(data)

def main():
    data = load_submissions()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "--status":
            print(f"\n📊 Web3 Opportunity Tracker")
            print(f"Last check: {data.get('last_check', 'Never')}")
            print(f"Tracked: {len(data['opportunities'])}")
            print(f"Submitted: {len(data['submitted'])}")
            return
        
        if cmd == "--submit":
            # Mark an opportunity as submitted
            if len(sys.argv) > 2:
                title = " ".join(sys.argv[2:])
                data = load_submissions()
                for opp in data["opportunities"]:
                    if opp["title"] in title or title in opp["title"]:
                        data["submitted"].append({
                            **opp,
                            "submitted_at": datetime.now().isoformat()
                        })
                        data["opportunities"].remove(opp)
                        save_submissions(data)
                        print(f"✅ Marked as submitted: {opp['title'][:50]}")
                        return
            print("Usage: python3 web3_scraper.py --submit <task title>")
            return
        
        if cmd == "add":
            # Add opportunity from command line
            if len(sys.argv) > 3:
                title = sys.argv[2]
                description = sys.argv[3]
                url = sys.argv[4] if len(sys.argv) > 4 else ""
                source = sys.argv[5] if len(sys.argv) > 5 else "manual"
                priority = sys.argv[6] if len(sys.argv) > 6 else "medium"
                add_manual_opportunity(title, description, url, source, priority)
            else:
                print("Usage: python3 web3_scraper.py add \"Title\" \"Description\" [url] [source] [priority]")
            return
        
        if cmd == "--list":
            print(f"\n📋 Tracked Opportunities:")
            for opp in data.get("opportunities", []):
                status = "🔴" if opp.get("priority") == "high" else "🟡"
                print(f"  {status} {opp['title'][:50]}")
            return
        
        if cmd == "--help":
            print("""
Web3 Opportunity Scraper Commands:
  python3 web3_scraper.py              - Run scanner, show queries
  python3 web3_scraper.py --status     - Show tracker status
  python3 web3_scraper.py --list       - List tracked opportunities
  python3 web3_scraper.py add "Title" "Desc" [url] [source] [priority]
  python3 web3_scraper.py --submit "Title" - Mark as submitted
  
Examples:
  python3 web3_scraper.py add "ETHGlobal Tokyo" "Hackathon in Tokyo" https://ethglobal.com ethglobal high
  python3 web3_scraper.py --submit "ETHGlobal Tokyo"
""")
            return
    
    run_search()

if __name__ == '__main__':
    main()
