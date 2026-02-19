# 🌐 Web3 Opportunity Tracker

> Automated discovery and tracking for Web3 hackathons, grants, jobs, and BD opportunities.

A CLI-powered system that scrapes Telegram channels, tracks hackathon submissions, manages prospects, and automates your Web3 opportunity pipeline.

## Features

- **Hackathon Tracker** — Track deadlines, submissions, and opportunities
- **Telegram Channel Scraper** — Monitor crypto/Web3 channels for BD leads
- **Prospect Manager** — CRM-style tracking for potential partners
- **SQLite Persistence** — All data stored locally
- **CLI-First** — Lightweight, scriptable, bot-friendly

## Installation

```bash
git clone https://github.com/mallocinfinity/web3-opportunity-tracker.git
cd web3-opportunity-tracker
pip install -r requirements.txt
```

## Usage

### Web3 Opportunity Scanner
```bash
python web3_scraper.py              # Run scanner
python web3_scraper.py --status      # Show tracker status
python web3_scraper.py --list        # List opportunities
python web3_scraper.py add "ETHGlobal" "Hackathon in Tokyo" https://ethglobal.com ethglobal high
python web3_scraper.py --submit "ETHGlobal"
```

### Telegram Channel Tracker
```bash
python telegram_scraper.py --add cryptoBD marketing
python telegram_scraper.py --list
python telegram_scraper.py --scrape
```

### Prospect CRM
```bash
python prospect_tracker.py add "John Doe" "CEO" "CryptoCo" "" "@cryptoBD" "Met at ETHCC" high
python prospect_tracker.py list
python prospect_tracker.py done 1
```

## Project Structure

```
web3-opportunity-tracker/
├── web3_scraper.py        # Hackathon & opportunity discovery
├── telegram_scraper.py    # Telegram channel monitoring
├── prospect_tracker.py    # BD prospect CRM
├── task_tracker.py        # Core task management
├── autonomous_tracker.py  # AI-powered task prioritization
├── submissions.json       # Tracked opportunities
├── prospects.json         # BD prospects
├── telegram_channels.json # Monitored channels
└── tasks.db              # SQLite database
```

## Tech Stack

- **Python 3.10+**
- **SQLite** — Local persistence
- **Subprocess** — Tool integration
- **JSON** — Configuration & data export

## Use Cases

- **Hackathon Pipelines** — Never miss a deadline
- **Grant Tracking** — Monitor L1/L2 ecosystem grants
- **BD Automation** — Surface opportunities from Telegram
- **Job Hunting** — Track defi/ethereuem postings

## License

ISC

---

**Demo:** Track opportunities in real-time | **Contact:** @evanw on Telegram
