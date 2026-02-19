# 🌐 Web3 Opportunity Tracker — Hackathon Submission

**Repository:** https://github.com/mallocinfinity/web3-opportunity-tracker

---

## EasyA Consensus Hong Kong 2026 Hackathon

### Project Name
**Web3 Opportunity Tracker** — Automated Discovery & CRM for Web3 Builders

### Team
- **Solo Dev:** Evan (@evanw)

### One-Line Pitch
CLI-powered system that automatically discovers hackathons, grants, and jobs — then tracks your prospects from Telegram channels to submission.

### Problem
Web3 builders miss opportunities because:
- Hackathon deadlines are scattered across dozens of sites
- Telegram channels are the real-time source for BD leads but untracked
- No unified system to track prospects → applications → outcomes

### Solution
A modular CLI toolkit that:
1. **Scans** for hackathons, grants, and jobs via queryable system
2. **Scrapes** Telegram channels for BD prospects
3. **Tracks** everything in SQLite with CRM-style pipeline
4. **Exports** to Google Sheets for outreach

### Tech Stack
- Python 3.10+ (stdlib + sqlite3)
- SQLite for persistence
- JSON for config/export
- No external dependencies

### Demo
```bash
# Track a hackathon opportunity
python web3_scraper.py add "ETHGlobal Tokyo" "Hackathon in Tokyo" https://ethglobal.com ethglobal high

# Monitor Telegram channels
python telegram_scraper.py --add cryptoBD marketing

# Export prospects to Google Sheets
python prospect_tracker.py export
```

### Differentiation
- **First-mover:** No existing tool combines hackathon discovery + Telegram scraping + prospect CRM
- **Lightweight:** Zero dependencies, runs anywhere
- **Hackathon-native:** Built by someone who actually applies to these

### What We're Building Next
- Webhook integrations (Discord/Slack alerts)
- AI-powered opportunity ranking
- Browser-based dashboard

---

## DoraHacks Submission

### Project Name
**Web3 Opportunity Tracker**

### Category
🛠️ **Developer Tools** / Web3 Infrastructure

### Team
Evan (@evanw) — Solo builder

### Submission URL
https://github.com/mallocinfinity/web3-opportunity-tracker

### Description
Automated discovery and tracking system for Web3 hackathons, grants, jobs, and BD opportunities. Built for builders who need to track deadlines, scrape Telegram for leads, and manage prospects — all from CLI.

### Problem
Web3 opportunities are fragmented. Hackathons live on dozens of sites. Real-time leads live in Telegram channels. No existing tool ties this together.

### Solution
- **web3_scraper.py** — Query system for hackathons, grants, jobs
- **telegram_scraper.py** — Channel monitoring for BD leads  
- **prospect_tracker.py** — CRM with Google Sheets export
- **task_tracker.py** — Personal task pipeline with autonomous prioritization

### Impact
Democratizes opportunity access for solo builders and small teams who can't afford expensive BD tools.

### Demo Video
[ADD_YOUTUBE_LINK]

### Why This Project?
I actually use this myself to track hackathon submissions. Built it because nothing else existed that combined discovery + scraping + CRM in one CLI tool.

### License
ISC

---

## Quick Start

```bash
git clone https://github.com/mallocinfinity/web3-opportunity-tracker.git
cd web3-opportunity-tracker

# Track an opportunity
python web3_scraper.py add "Protocol Labs Grant" "RFP for compute" https://protocol.ai grants high

# Add Telegram channel
python telegram_scraper.py --add defijobs

# Export to Sheets
python prospect_tracker.py export
```

### Files
- `web3_scraper.py` — Opportunity discovery
- `telegram_scraper.py` — Channel monitoring
- `prospect_tracker.py` — CRM with export
- `task_tracker.py` — Task pipeline
- `autonomous_tracker.py` — AI prioritization

---

**Contact:** @evanw on Telegram  
**GitHub:** https://github.com/mallocinfinity/web3-opportunity-tracker
