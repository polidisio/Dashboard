#!/usr/bin/env python3
"""
Dashboard - Personal Knowledge Base
A simple web app to store and view messages, quotes, and notes.
Can be deployed on any Linux server.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import os
from datetime import datetime, timedelta
import json
import urllib.request
import urllib.parse

app = Flask(__name__)
DATABASE = 'dashboard.db'

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Messages table
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            source TEXT DEFAULT 'telegram',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tags TEXT,
            is_important INTEGER DEFAULT 0
        )
    ''')
    
    # Quotes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            author TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Projects table
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Notes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Daily logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def save_message(content, source='telegram', tags=''):
    """Save a message to the database."""
    conn = get_db_connection()
    conn.execute('INSERT INTO messages (content, source, tags) VALUES (?, ?, ?)',
               (content, source, tags))
    conn.commit()
    conn.close()

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main dashboard."""
    conn = get_db_connection()
    
    # Get stats
    messages_count = conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
    quotes_count = conn.execute('SELECT COUNT(*) FROM quotes').fetchone()[0]
    projects_count = conn.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
    notes_count = conn.execute('SELECT COUNT(*) FROM notes').fetchone()[0]
    
    # Get recent items
    recent_messages = conn.execute('SELECT * FROM messages ORDER BY created_at DESC LIMIT 5').fetchall()
    recent_quotes = conn.execute('SELECT * FROM quotes ORDER BY created_at DESC LIMIT 3').fetchall()
    active_projects = conn.execute("SELECT * FROM projects WHERE status = 'active' ORDER BY updated_at DESC LIMIT 5").fetchall()
    
    # Get today's messages
    today_messages = conn.execute('''
        SELECT * FROM messages 
        WHERE date(created_at) = date('now') 
        ORDER BY created_at DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('index.html',
                         messages_count=messages_count,
                         quotes_count=quotes_count,
                         projects_count=projects_count,
                         notes_count=notes_count,
                         recent_messages=recent_messages,
                         recent_quotes=recent_quotes,
                         active_projects=active_projects,
                         today_messages=today_messages)

# ==================== MESSAGES ====================

@app.route('/messages')
def messages():
    """Messages list grouped by day."""
    conn = get_db_connection()
    messages = conn.execute('SELECT * FROM messages ORDER BY created_at DESC').fetchall()
    
    # Group by date
    messages_by_date = {}
    for msg in messages:
        date_key = msg['created_at'][:10]  # YYYY-MM-DD
        if date_key not in messages_by_date:
            messages_by_date[date_key] = []
        messages_by_date[date_key].append(msg)
    
    conn.close()
    return render_template('messages.html', messages_by_date=messages_by_date)

@app.route('/messages/add', methods=['POST'])
def add_message():
    """Add a new message."""
    content = request.form.get('content', '')
    source = request.form.get('source', 'telegram')
    tags = request.form.get('tags', '')
    
    if content:
        conn = get_db_connection()
        conn.execute('INSERT INTO messages (content, source, tags) VALUES (?, ?, ?)',
                   (content, source, tags))
        conn.commit()
        conn.close()
    
    return redirect(url_for('messages'))

@app.route('/api/messages', methods=['GET', 'POST'])
def api_messages():
    """API for messages."""
    conn = get_db_connection()
    
    if request.method == 'POST':
        data = request.get_json()
        conn.execute('INSERT INTO messages (content, source, tags) VALUES (?, ?, ?)',
                   (data.get('content', ''), data.get('source', 'api'), data.get('tags', '')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    # Get messages by date range
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = 'SELECT * FROM messages'
    params = []
    
    if date_from and date_to:
        query += ' WHERE date(created_at) BETWEEN ? AND ?'
        params = [date_from, date_to]
    elif date_from:
        query += ' WHERE date(created_at) >= ?'
        params = [date_from]
    elif date_to:
        query += ' WHERE date(created_at) <= ?'
        params = [date_to]
    
    query += ' ORDER BY created_at DESC LIMIT 100'
    
    messages = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in messages])

@app.route('/messages/delete/<int:id>', methods=['POST'])
def delete_message(id):
    """Delete a message."""
    conn = get_db_connection()
    conn.execute('DELETE FROM messages WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('messages'))

# ==================== QUOTES ====================

@app.route('/quotes')
def quotes_page():
    """Quotes list."""
    conn = get_db_connection()
    quotes = conn.execute('SELECT * FROM quotes ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('quotes.html', quotes=quotes)

@app.route('/quotes/add', methods=['POST'])
def add_quote():
    """Add a new quote."""
    content = request.form.get('content', '')
    author = request.form.get('author', '')
    source = request.form.get('source', '')
    
    if content:
        conn = get_db_connection()
        conn.execute('INSERT INTO quotes (content, author, source) VALUES (?, ?, ?)',
                   (content, author, source))
        conn.commit()
        conn.close()
    
    return redirect(url_for('quotes_page'))

# ==================== PROJECTS ====================

@app.route('/projects')
def projects_page():
    """Projects list."""
    conn = get_db_connection()
    projects = conn.execute('SELECT * FROM projects ORDER BY updated_at DESC').fetchall()
    conn.close()
    return render_template('projects.html', projects=projects)

@app.route('/projects/add', methods=['POST'])
def add_project():
    """Add a new project."""
    name = request.form.get('name', '')
    description = request.form.get('description', '')
    
    if name:
        conn = get_db_connection()
        conn.execute('INSERT INTO projects (name, description) VALUES (?, ?)',
                   (name, description))
        conn.commit()
        conn.close()
    
    return redirect(url_for('projects_page'))

# ==================== NOTES ====================

@app.route('/notes')
def notes_page():
    """Notes list."""
    conn = get_db_connection()
    notes = conn.execute('SELECT * FROM notes ORDER BY updated_at DESC').fetchall()
    conn.close()
    return render_template('notes.html', notes=notes)

@app.route('/notes/add', methods=['POST'])
def add_note():
    """Add a new note."""
    title = request.form.get('title', '')
    content = request.form.get('content', '')
    category = request.form.get('category', '')
    
    if title:
        conn = get_db_connection()
        conn.execute('INSERT INTO notes (title, content, category) VALUES (?, ?, ?)',
                   (title, content, category))
        conn.commit()
        conn.close()
    
    return redirect(url_for('notes_page'))

# ==================== SEARCH ====================

@app.route('/api/search')
def search():
    """Search across all items."""
    query = request.args.get('q', '')
    results = {'messages': [], 'quotes': [], 'projects': [], 'notes': []}
    
    if query:
        conn = get_db_connection()
        
        results['messages'] = conn.execute(
            "SELECT * FROM messages WHERE content LIKE ? OR tags LIKE ? LIMIT 20", 
            (f'%{query}%', f'%{query}%')
        ).fetchall()
        
        results['quotes'] = conn.execute(
            "SELECT * FROM quotes WHERE content LIKE ? OR author LIKE ? LIMIT 10", 
            (f'%{query}%', f'%{query}%')
        ).fetchall()
        
        results['projects'] = conn.execute(
            "SELECT * FROM projects WHERE name LIKE ? OR description LIKE ? LIMIT 10", 
            (f'%{query}%', f'%{query}%')
        ).fetchall()
        
        results['notes'] = conn.execute(
            "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? LIMIT 10", 
            (f'%{query}%', f'%{query}%')
        ).fetchall()
        
        conn.close()
    
    return jsonify({k: [dict(ix) for ix in v] for k, v in results.items()})

# ==================== AUTO-SAVE FROM TELEGRAM ====================

@app.route('/api/telegram/save', methods=['POST'])
def telegram_save():
    """Endpoint to save messages from Telegram."""
    data = request.get_json()
    content = data.get('content', '')
    tags = data.get('tags', '')
    
    if content:
        save_message(content, source='telegram', tags=tags)
        return jsonify({'success': True, 'message': 'Saved!'})
    
    return jsonify({'success': False, 'error': 'No content'}), 400

# ==================== MAIN ====================

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("🌐 Dashboard iniciado!")
    print("   http://localhost:5001")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
