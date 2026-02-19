#!/usr/bin/env python3
"""
Prospect Research & Outreach Tracker
Creates Google Sheets-ready data for client prospecting

Usage:
    python3 prospect_tracker.py --sheet           # Generate TSV for Google Sheets import
    python3 prospect_tracker.py add "Name" "role" "company" "email" "source" "notes"
    python3 prospect_tracker.py status            # Show prospect stats
    python3 prospect_tracker.py export            # Export for Sheets import
"""

import json
import csv
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

# Paths
SCRIPT_DIR = Path(__file__).parent
PROSPECTS_FILE = SCRIPT_DIR / "prospects.json"
EXPORT_DIR = SCRIPT_DIR / "exports"

def load_prospects():
    """Load existing prospects from JSON"""
    if PROSPECTS_FILE.exists():
        with open(PROSPECTS_FILE, 'r') as f:
            return json.load(f)
    return {
        "last_updated": None,
        "prospects": [],
        "stats": {
            "total": 0,
            "contacted": 0,
            "replied": 0,
            "meetings": 0
        }
    }

def save_prospects(data):
    """Save prospects to JSON"""
    data["last_updated"] = datetime.now().isoformat()
    with open(PROSPECTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_prospect(name, role, company, email, source, notes="", priority="medium"):
    """Add a new prospect"""
    data = load_prospects()
    
    prospect = {
        "id": len(data["prospects"]) + 1,
        "name": name,
        "role": role,
        "company": company,
        "email": email or "N/A",
        "source": source,
        "notes": notes,
        "priority": priority,
        "status": "new",  # new, contacted, replied, meeting, won, lost
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    data["prospects"].append(prospect)
    data["stats"]["total"] = len(data["prospects"])
    save_prospects(data)
    
    print(f"  ✅ Added: {name} ({role} at {company})")
    return prospect

def update_status(prospect_id, new_status):
    """Update prospect status"""
    data = load_prospects()
    for p in data["prospects"]:
        if p["id"] == prospect_id:
            p["status"] = new_status
            p["updated_at"] = datetime.now().isoformat()
            save_prospects(data)
            print(f"  ✅ Updated {p['name']} → {new_status}")
            return
    
    print(f"  ❌ Prospect {prospect_id} not found")

def generate_tsv():
    """Generate TSV for Google Sheets import"""
    data = load_prospects()
    
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = EXPORT_DIR / "prospects_outreach.tsv"
    
    headers = ["ID", "Name", "Role", "Company", "Email", "Source", "Priority", "Status", "Notes", "Created"]
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(headers)
        for p in data["prospects"]:
            writer.writerow([
                p["id"],
                p["name"],
                p["role"],
                p["company"],
                p["email"],
                p["source"],
                p["priority"],
                p["status"],
                p["notes"][:200] if p["notes"] else "",
                p["created_at"][:10]
            ])
    
    print(f"\n📊 TSV exported to: {filepath}")
    print(f"   {len(data['prospects'])} prospects ready for import")
    return filepath

def show_status():
    """Show prospect tracking status"""
    data = load_prospects()
    last_updated = data.get("last_updated")
    
    print(f"\n📊 Prospect Tracker")
    print(f"   Last updated: {last_updated[:19] if last_updated else 'Never'}")
    print(f"   Total prospects: {data['stats']['total']}")
    print(f"   Contacted: {data['stats']['contacted']}")
    print(f"   Replied: {data['stats']['replied']}")
    print(f"   Meetings: {data['stats']['meetings']}")
    
    # Show recent prospects
    if data["prospects"]:
        print(f"\n📋 Recent Prospects:")
        for p in data["prospects"][-5:]:
            status_emoji = {"new": "🆕", "contacted": "📧", "replied": "✅", "meeting": "📅", "won": "🎉", "lost": "❌"}
            emoji = status_emoji.get(p["status"], "📋")
            print(f"   {emoji} {p['name']} ({p['role']} at {p['company']}) - {p['source']}")

def main():
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "--status" or cmd == "status":
            show_status()
            return
        
        if cmd == "--export" or cmd == "export":
            generate_tsv()
            return
        
        if cmd == "add":
            if len(sys.argv) > 6:
                name = sys.argv[2]
                role = sys.argv[3]
                company = sys.argv[4]
                email = sys.argv[5]
                source = sys.argv[6] if len(sys.argv) > 6 else "manual"
                notes = sys.argv[7] if len(sys.argv) > 7 else ""
                priority = sys.argv[8] if len(sys.argv) > 8 else "medium"
                add_prospect(name, role, company, email, source, notes, priority)
            else:
                print("Usage: python3 prospect_tracker.py add \"Name\" \"Role\" \"Company\" \"email@example.com\" \"source\" [notes] [priority]")
            return
        
        if cmd == "--update":
            if len(sys.argv) > 3:
                update_status(int(sys.argv[2]), sys.argv[3])
            else:
                print("Usage: python3 prospect_tracker.py --update <id> <new_status>")
            return
        
        if cmd == "--help" or cmd == "help":
            print("""
Prospect Tracker Commands:
  python3 prospect_tracker.py status          - Show tracking status
  python3 prospect_tracker.py export          - Generate TSV for Google Sheets
  python3 prospect_tracker.py add "Name" "Role" "Company" "email" "source" [notes] [priority]
  python3 prospect_tracker.py --update <id> <status>
  
Examples:
  python3 prospect_tracker.py add "John Doe" "CEO" "Acme Inc" "john@acme.com" "LinkedIn" "Met at ETHDenver" high
  python3 prospect_tracker.py --update 3 replied
  python3 prospect_tracker.py export

Import to Google Sheets:
  1. Open Google Sheets
  2. File → Import → Upload → select prospects_outreach.tsv
  3. Separator: Tab, Import action: Create new spreadsheet
""")
            return
    
    show_status()
    print("\n💡 Run 'python3 prospect_tracker.py export' to generate TSV for Google Sheets")

if __name__ == '__main__':
    main()
