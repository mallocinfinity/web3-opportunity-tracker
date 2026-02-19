#!/usr/bin/env python3
"""
Task Tracker - A simple CLI task management app
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__name__).parent / "tasks.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

def add_task(title, description="", priority="medium"):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('INSERT INTO tasks (title, description, priority, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
              (title, description, priority, now, now))
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    print(f"✓ Task created: {title} (ID: {task_id})")

def list_tasks(status=None):
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
        return
    
    print(f"\n{'ID':<4} {'Status':<10} {'Priority':<8} {'Title':<30}")
    print("-" * 60)
    for task in tasks:
        print(f"{task[0]:<4} {task[3]:<10} {task[4]:<8} {task[1][:28]:<30}")

def update_task(task_id, title=None, description=None, status=None, priority=None):
    conn = get_connection()
    c = conn.cursor()
    updates = []
    values = []
    now = datetime.now().isoformat()
    
    if title:
        updates.append('title = ?')
        values.append(title)
    if description is not None:
        updates.append('description = ?')
        values.append(description)
    if status:
        updates.append('status = ?')
        values.append(status)
    if priority:
        updates.append('priority = ?')
        values.append(priority)
    updates.append('updated_at = ?')
    values.append(now)
    values.append(task_id)
    
    if updates:
        c.execute(f'UPDATE tasks SET {", ".join(updates)} WHERE id = ?', values)
        conn.commit()
        print(f"✓ Task {task_id} updated")
    else:
        print("No changes made.")
    conn.close()

def delete_task(task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    print(f"✓ Task {task_id} deleted")

def show_help():
    print("""
Task Tracker Commands:
  add "title" [description] [--priority low|medium|high]
  list [pending|completed|all]
  done <id>
  delete <id>
  show <id>
  help

Examples:
  python task_tracker.py add "Buy groceries" "milk, eggs, bread" --priority high
  python task_tracker.py list pending
  python task_tracker.py done 3
  python task_tracker.py delete 5
""")

def show_task(task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = c.fetchone()
    conn.close()
    
    if task:
        print(f"\nTask #{task[0]}")
        print(f"Title: {task[1]}")
        print(f"Description: {task[2] or '(none)'}")
        print(f"Status: {task[3]}")
        print(f"Priority: {task[4]}")
        print(f"Created: {task[5]}")
        print(f"Updated: {task[6]}")
    else:
        print(f"Task {task_id} not found.")

def main():
    init_db()
    
    args = sys.argv[1:]
    
    if not args or args[0] == 'help':
        show_help()
        return
    
    cmd = args[0]
    
    if cmd == 'add':
        if len(args) < 2:
            print("Error: 'add' requires a title")
            return
        title = args[1]
        description = ""
        priority = "medium"
        
        # Parse remaining args
        i = 2
        while i < len(args):
            if args[i] == '--priority' and i + 1 < len(args):
                priority = args[i + 1].lower()
                i += 2
            else:
                if description:
                    description += " " + args[i]
                else:
                    description = args[i]
                i += 1
        
        add_task(title, description, priority)
    
    elif cmd == 'list':
        status = args[1] if len(args) > 1 else None
        if status and status not in ['pending', 'completed']:
            status = None
        list_tasks(status if status else None)
    
    elif cmd == 'done':
        if len(args) < 2:
            print("Error: 'done' requires a task ID")
            return
        try:
            task_id = int(args[1])
            update_task(task_id, status='completed')
        except ValueError:
            print("Error: Task ID must be a number")
    
    elif cmd == 'delete':
        if len(args) < 2:
            print("Error: 'delete' requires a task ID")
            return
        try:
            task_id = int(args[1])
            delete_task(task_id)
        except ValueError:
            print("Error: Task ID must be a number")
    
    elif cmd == 'show':
        if len(args) < 2:
            print("Error: 'show' requires a task ID")
            return
        try:
            task_id = int(args[1])
            show_task(task_id)
        except ValueError:
            print("Error: Task ID must be a number")
    
    else:
        print(f"Unknown command: {cmd}")
        show_help()

if __name__ == '__main__':
    main()
