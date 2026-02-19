#!/usr/bin/env python3
"""
Autonomous Agent Task Tracker
Enhanced with dependencies, ROI scoring, and state machine
"""

import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from enum import Enum

DB_PATH = Path(__file__).parent / "tasks.db"

class TaskStatus(Enum):
    PENDING = "pending"      # Not yet ready (dependencies not met)
    ELIGIBLE = "eligible"   # Ready to work on
    IN_PROGRESS = "in_progress"
    REVIEW = "review"        # Awaiting verification
    DONE = "completed"

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Main tasks table with autonomy fields
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            
            -- Dependencies
            prerequisites TEXT,  -- JSON array of task IDs
            
            -- ROI Scoring (0-10 scale)
            impact_score INTEGER DEFAULT 5,      -- Revenue/user impact
            urgency_score INTEGER DEFAULT 5,    -- Time sensitivity
            effort_score INTEGER DEFAULT 5,     -- 1=hours, 10=weeks
            
            -- Auto-complete rules
            auto_complete BOOLEAN DEFAULT FALSE,
            completion_criteria TEXT,          -- What defines "done"
            
            -- Metadata
            created_at TEXT,
            updated_at TEXT,
            started_at TEXT,
            completed_at TEXT,
            created_by TEXT DEFAULT 'agent'
        )
    ''')
    
    # Decision log for learning
    c.execute('''
        CREATE TABLE IF NOT EXISTS decision_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            decision TEXT,
            reasoning TEXT,
            outcome TEXT,  -- success, failed, blocked
            created_at TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    ''')
    
    # Event log for webhook triggers
    c.execute('''
        CREATE TABLE IF NOT EXISTS event_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            payload TEXT,
            handled BOOLEAN DEFAULT FALSE,
            created_at TEXT
        )
    ''')
    
    # Goals table for high-level business objectives
    c.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            source TEXT DEFAULT 'user',
            tasks_generated BOOLEAN DEFAULT FALSE,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    # Manager approvals for sensitive actions
    c.execute('''
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            session_key TEXT,
            requested_at_ms INTEGER,
            decided_at_ms INTEGER,
            decision_text TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    ''')

    # Inbound message tracking (e.g., Telegram goal intake)
    c.execute('''
        CREATE TABLE IF NOT EXISTS inbound_state (
            session_key TEXT PRIMARY KEY,
            last_ts INTEGER DEFAULT 0,
            updated_at TEXT
        )
    ''')

    # Approval batching state per session
    c.execute('''
        CREATE TABLE IF NOT EXISTS approval_state (
            session_key TEXT PRIMARY KEY,
            last_batch_sent_ms INTEGER DEFAULT 0,
            updated_at TEXT
        )
    ''')

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)


# ── Goal management ──

def add_goal(description, source="user"):
    """Add a high-level goal."""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
        INSERT INTO goals (description, status, source, tasks_generated, created_at, updated_at)
        VALUES (?, 'active', ?, FALSE, ?, ?)
    ''', (description, source, now, now))
    goal_id = c.lastrowid
    conn.commit()
    conn.close()
    print(f"Goal added: {description} (ID: {goal_id})")
    return goal_id


def get_active_goals():
    """Get all active goals."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, description, status, source, tasks_generated, created_at, updated_at FROM goals WHERE status = 'active'")
    goals = c.fetchall()
    conn.close()
    return goals


def get_untasked_goals():
    """Get active goals that haven't been decomposed into tasks yet."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, description, status, source, tasks_generated, created_at, updated_at FROM goals WHERE status = 'active' AND tasks_generated = FALSE")
    goals = c.fetchall()
    conn.close()
    return goals


def mark_goal_tasked(goal_id):
    """Mark a goal as having been decomposed into tasks."""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("UPDATE goals SET tasks_generated = TRUE, updated_at = ? WHERE id = ?", (now, goal_id))
    conn.commit()
    conn.close()


def complete_goal(goal_id):
    """Mark a goal as completed."""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("UPDATE goals SET status = 'completed', updated_at = ? WHERE id = ?", (now, goal_id))
    conn.commit()
    conn.close()
    print(f"Goal {goal_id} completed")

def add_task(title, description="", priority="medium", 
             prerequisites=None, impact=5, urgency=5, effort=5,
             auto_complete=False, criteria=""):
    """
    Add a new task with full autonomy metadata
    """
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    prereq_json = ",".join([str(p) for p in (prerequisites or [])])
    
    c.execute('''
        INSERT INTO tasks (
            title, description, status, priority,
            prerequisites, impact_score, urgency_score, effort_score,
            auto_complete, completion_criteria,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        title, description, TaskStatus.PENDING.value, priority,
        prereq_json, impact, urgency, effort,
        auto_complete, criteria,
        now, now
    ))
    
    task_id = c.lastrowid
    
    # Check if prerequisites are met
    if not prerequisites:
        c.execute('UPDATE tasks SET status = ? WHERE id = ?', 
                  (TaskStatus.ELIGIBLE.value, task_id))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Task created: {title} (ID: {task_id})")
    return task_id

def list_tasks(status=None, sort_by="roi"):
    """
    List tasks with ROI-based sorting
    ROI = impact × urgency ÷ effort
    """
    conn = get_connection()
    c = conn.cursor()
    
    if status:
        c.execute('SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC', (status,))
    else:
        c.execute('SELECT * FROM tasks ORDER BY created_at DESC')
    
    tasks = c.fetchall()
    conn.close()
    
    if not tasks:
        print("No tasks found.")
        return []
    
    # Calculate ROI for sorting
    task_list = []
    for task in tasks:
        t = {
            'id': task[0],
            'title': task[1],
            'status': task[3],
            'priority': task[4],
            'prerequisites': task[5],
            'impact': task[6],
            'urgency': task[7],
            'effort': task[8],
        }
        
        # ROI = impact × urgency ÷ effort
        t['roi_score'] = (t['impact'] * t['urgency']) / max(t['effort'], 1)
        task_list.append(t)
    
    # Sort by ROI (highest first)
    if sort_by == "roi":
        task_list.sort(key=lambda x: x['roi_score'], reverse=True)
    
    print(f"\n{'ID':<4} {'Status':<10} {'Priority':<8} {'ROI':<6} {'Title':<35}")
    print("-" * 70)
    for t in task_list:
        status_emoji = {"pending": "⏳", "eligible": "✅", "in_progress": "🔄", "review": "👀", "completed": "✓"}
        emoji = status_emoji.get(t['status'], "  ")
        print(f"{t['id']:<4} {emoji} {t['status']:<9} {t['priority']:<8} {t['roi_score']:<6.1f} {t['title'][:33]:<35}")
    
    return task_list

def get_eligible_tasks():
    """Get tasks ready to work on (dependencies met)"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('SELECT * FROM tasks WHERE status = ? ORDER BY (impact_score * urgency_score / effort_score) DESC', 
              (TaskStatus.ELIGIBLE.value,))
    
    tasks = c.fetchall()
    conn.close()
    return tasks

def check_prerequisites(task_id):
    """Check if all prerequisites are completed"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT prerequisites FROM tasks WHERE id = ?', (task_id,))
    row = c.fetchone()
    conn.close()
    
    if not row or not row[0]:
        return True, []
    
    prereq_ids = [int(x) for x in row[0].split(',') if x.strip()]
    
    conn = get_connection()
    c = conn.cursor()
    pending = []
    for pid in prereq_ids:
        c.execute('SELECT status FROM tasks WHERE id = ?', (pid,))
        status = c.fetchone()
        if not status or status[0] != TaskStatus.DONE.value:
            pending.append(pid)
    
    conn.close()
    return len(pending) == 0, pending

def start_task(task_id):
    """Start a task if eligible"""
    eligible, pending = check_prerequisites(task_id)
    
    if not eligible:
        print(f"❌ Task {task_id} blocked by: {pending}")
        return False
    
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
        UPDATE tasks SET status = ?, started_at = ?, updated_at = ?
        WHERE id = ?
    ''', (TaskStatus.IN_PROGRESS.value, now, now, task_id))
    conn.commit()
    conn.close()
    
    print(f"🔄 Started task {task_id}")
    return True

def complete_task(task_id, criteria_met=True):
    """Mark task as done"""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
        UPDATE tasks SET status = ?, completed_at = ?, updated_at = ?
        WHERE id = ?
    ''', (TaskStatus.DONE.value, now, now, task_id))
    conn.commit()
    
    # Check other tasks - some may now be eligible
    c.execute('SELECT id, prerequisites FROM tasks WHERE status = ?', (TaskStatus.PENDING.value,))
    pending_tasks = c.fetchall()
    conn.close()
    
    for task_id, prereqs in pending_tasks:
        if prereqs:
            prereq_list = [int(x) for x in prereqs.split(',') if x.strip()]
            if task_id in prereq_list:
                eligible, _ = check_prerequisites(task_id)
                if eligible:
                    mark_eligible(task_id)
    
    print(f"✓ Completed task {task_id}")

def mark_eligible(task_id):
    """Mark a task as eligible for work"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE tasks SET status = ? WHERE id = ?', 
              (TaskStatus.ELIGIBLE.value, task_id))
    conn.commit()
    conn.close()
    print(f"✅ Task {task_id} is now eligible")

def mark_review(task_id):
    """Mark a task as in review (awaiting approval)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE tasks SET status = ? WHERE id = ?', 
              (TaskStatus.REVIEW.value, task_id))
    conn.commit()
    conn.close()
    print(f"👀 Task {task_id} is now in review")

def mark_eligible_if_ready(task_id):
    """Mark task eligible if prerequisites are met, otherwise pending."""
    eligible, _ = check_prerequisites(task_id)
    conn = get_connection()
    c = conn.cursor()
    next_status = TaskStatus.ELIGIBLE.value if eligible else TaskStatus.PENDING.value
    c.execute('UPDATE tasks SET status = ? WHERE id = ?', (next_status, task_id))
    conn.commit()
    conn.close()
    if eligible:
        print(f"✅ Task {task_id} is now eligible")
    else:
        print(f"⏳ Task {task_id} is now pending prerequisites")

def log_decision(task_id, decision, reasoning, outcome=""):
    """Log a decision for learning"""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
        INSERT INTO decision_log (task_id, decision, reasoning, outcome, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (task_id, decision, reasoning, outcome, now))
    conn.commit()
    conn.close()

def log_event(event_type, payload):
    """Log an event from webhooks"""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
        INSERT INTO event_log (event_type, payload, created_at)
        VALUES (?, ?, ?)
    ''', (event_type, payload, now))
    conn.commit()
    conn.close()

# ── Approval tracking ──

def create_approval_request(task_id, session_key=None):
    conn = get_connection()
    c = conn.cursor()
    now_iso = datetime.now().isoformat()
    now_ms = int(time.time() * 1000)
    c.execute('''
        INSERT INTO approvals (
            task_id, status, session_key, requested_at_ms,
            created_at, updated_at
        ) VALUES (?, 'pending', ?, ?, ?, ?)
    ''', (task_id, session_key, now_ms, now_iso, now_iso))
    conn.commit()
    conn.close()

def get_approval(task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT task_id, status, session_key, requested_at_ms, decided_at_ms, decision_text
        FROM approvals
        WHERE task_id = ?
        ORDER BY id DESC
        LIMIT 1
    ''', (task_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "task_id": row[0],
        "status": row[1],
        "session_key": row[2],
        "requested_at_ms": row[3] or 0,
        "decided_at_ms": row[4] or 0,
        "decision_text": row[5] or "",
    }

def get_pending_approvals():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT task_id, session_key, requested_at_ms
        FROM approvals
        WHERE status = 'pending'
        ORDER BY requested_at_ms ASC
    ''')
    rows = c.fetchall()
    conn.close()
    return [
        {"task_id": r[0], "session_key": r[1], "requested_at_ms": r[2] or 0}
        for r in rows
    ]

def resolve_approval(task_id, status, decision_text=""):
    conn = get_connection()
    c = conn.cursor()
    now_iso = datetime.now().isoformat()
    now_ms = int(time.time() * 1000)
    c.execute('''
        UPDATE approvals
        SET status = ?, decided_at_ms = ?, decision_text = ?, updated_at = ?
        WHERE task_id = ? AND status = 'pending'
    ''', (status, now_ms, decision_text[:500], now_iso, task_id))
    conn.commit()
    conn.close()

def get_inbound_last_ts(session_key):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT last_ts FROM inbound_state WHERE session_key = ?', (session_key,))
    row = c.fetchone()
    conn.close()
    if not row:
        return 0
    return int(row[0] or 0)

def set_inbound_last_ts(session_key, last_ts):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
        INSERT INTO inbound_state (session_key, last_ts, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(session_key) DO UPDATE SET
            last_ts = excluded.last_ts,
            updated_at = excluded.updated_at
    ''', (session_key, int(last_ts), now))
    conn.commit()
    conn.close()

def get_approval_state(session_key):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT last_batch_sent_ms FROM approval_state WHERE session_key = ?', (session_key,))
    row = c.fetchone()
    conn.close()
    if not row:
        return 0
    return int(row[0] or 0)

def set_approval_state(session_key, last_batch_sent_ms):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
        INSERT INTO approval_state (session_key, last_batch_sent_ms, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(session_key) DO UPDATE SET
            last_batch_sent_ms = excluded.last_batch_sent_ms,
            updated_at = excluded.updated_at
    ''', (session_key, int(last_batch_sent_ms), now))
    conn.commit()
    conn.close()

def get_next_best_task():
    """Decision engine: Pick highest ROI eligible task"""
    tasks = get_eligible_tasks()
    if not tasks:
        return None
    
    best = None
    best_roi = 0
    
    for task in tasks:
        roi = (task[6] * task[7]) / max(task[8], 1)  # impact × urgency ÷ effort
        if roi > best_roi:
            best_roi = roi
            best = task
    
    return best

def show_task(task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = c.fetchone()
    conn.close()
    
    if task:
        print(f"\n{'='*50}")
        print(f"Task #{task[0]}")
        print(f"Title: {task[1]}")
        print(f"Description: {task[2] or '(none)'}")
        print(f"Status: {task[3]}")
        print(f"Priority: {task[4]}")
        print(f"\nROI Metrics:")
        print(f"  Impact: {task[6]}/10  Urgency: {task[7]}/10  Effort: {task[8]}/10")
        print(f"  ROI Score: {(task[6] * task[7]) / max(task[8], 1):.1f}")
        print(f"\nDependencies:")
        print(f"  Prerequisites: {task[5] or 'None'}")
        print(f"\nTimestamps:")
        print(f"  Created: {task[10]}")
        print(f"  Started: {task[11] or 'Not started'}")
        print(f"  Completed: {task[12] or 'In progress'}")
        print(f"{'='*50}")
    else:
        print(f"Task {task_id} not found.")

def get_task(task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    row = c.fetchone()
    conn.close()
    return row

def main():
    init_db()
    
    args = sys.argv[1:]
    
    if not args or args[0] == 'help':
        print("""
╔══════════════════════════════════════════════════════════════╗
║           AUTONOMOUS AGENT TASK TRACKER                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Commands:                                                  ║
║    add "title" [desc] [flags]                              ║
║      --priority low|medium|high|critical                    ║
║      --impact 1-10         (revenue/user impact)           ║
║      --urgency 1-10        (time sensitivity)              ║
║      --effort 1-10         (1=hours, 10=weeks)            ║
║      --prereq 1,2,3        (task IDs)                     ║
║      --auto                 (auto-complete when criteria met)║
║      --criteria "text"      (what defines done)             ║
║                                                              ║
║    list [pending|eligible|in_progress|completed|all]        ║
║    next                                                  ║
║    start <id>                                             ║
║    done <id>                                              ║
║    show <id>                                              ║
║    decisions [task_id]                                    ║
║    events                                                 ║
║    help                                                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        return
    
    cmd = args[0]
    
    if cmd == 'add':
        title = args[1] if len(args) > 1 else ""
        description = ""
        priority = "medium"
        impact, urgency, effort = 5, 5, 5
        prereqs = []
        auto_complete = False
        criteria = ""
        
        i = 2
        while i < len(args):
            arg = args[i]
            if arg == '--priority' and i + 1 < len(args):
                priority = args[i + 1].lower()
                i += 2
            elif arg == '--impact' and i + 1 < len(args):
                impact = int(args[i + 1])
                i += 2
            elif arg == '--urgency' and i + 1 < len(args):
                urgency = int(args[i + 1])
                i += 2
            elif arg == '--effort' and i + 1 < len(args):
                effort = int(args[i + 1])
                i += 2
            elif arg == '--prereq' and i + 1 < len(args):
                prereqs = [int(x) for x in args[i + 1].split(',')]
                i += 2
            elif arg == '--auto':
                auto_complete = True
                i += 1
            elif arg == '--criteria' and i + 1 < len(args):
                criteria = args[i + 1]
                i += 2
            else:
                description += " " + args[i] if description else args[i]
                i += 1
        
        add_task(title, description, priority, prereqs, impact, urgency, effort, auto_complete, criteria)
    
    elif cmd == 'list':
        status = args[1] if len(args) > 1 else None
        if status and status not in ['pending', 'eligible', 'in_progress', 'review', 'completed']:
            status = None
        list_tasks(status if status else None)
    
    elif cmd == 'next':
        task = get_next_best_task()
        if task:
            print(f"\n🎯 Best next task: #{task[0]} - {task[1]}")
            print(f"   ROI: {(task[6] * task[7]) / max(task[8], 1):.1f}")
        else:
            print("No eligible tasks. Check pending tasks with dependencies.")
    
    elif cmd == 'start':
        if len(args) < 2:
            print("Error: 'start' requires task ID")
            return
        start_task(int(args[1]))
    
    elif cmd == 'done':
        if len(args) < 2:
            print("Error: 'done' requires task ID")
            return
        complete_task(int(args[1]))
    
    elif cmd == 'show':
        if len(args) < 2:
            print("Error: 'show' requires task ID")
            return
        show_task(int(args[1]))
    
    elif cmd == 'decisions':
        # Show recent decisions
        conn = get_connection()
        c = conn.cursor()
        if len(args) > 1:
            c.execute('SELECT * FROM decision_log WHERE task_id = ? ORDER BY created_at DESC', (args[1],))
        else:
            c.execute("SELECT * FROM decision_log ORDER BY created_at DESC LIMIT 20")
        decisions = c.fetchall()
        conn.close()
        for d in decisions:
            print(f"  Task {d[1]}: {d[2]} ({d[4] or 'pending'})")
    
    elif cmd == 'events':
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM event_log ORDER BY created_at DESC LIMIT 10')
        events = c.fetchall()
        conn.close()
        for e in events:
            print(f"  {e[3]}: {e[1]} - {e[2][:50]}")
    
    elif cmd == 'add-goal':
        if len(args) < 2:
            print("Error: 'add-goal' requires a description")
            return
        desc = " ".join(args[1:])
        add_goal(desc)

    elif cmd == 'goals':
        goals = get_active_goals()
        if not goals:
            print("No active goals.")
        else:
            print(f"\n{'ID':<4} {'Tasked':<7} {'Source':<8} {'Description':<50}")
            print("-" * 70)
            for g in goals:
                tasked = "Yes" if g[4] else "No"
                print(f"{g[0]:<4} {tasked:<7} {g[3]:<8} {g[1][:48]:<50}")

    else:
        print(f"Unknown command: {cmd}")
        print("Run 'help' for commands")

if __name__ == '__main__':
    main()
