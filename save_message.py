#!/usr/bin/env python3
"""
Save message to Dashboard
Usage: python save_message.py "Your message" "tag1,tag2"
"""

import sys
import requests
import json

def save_message(content, tags=''):
    url = 'http://192.168.1.223:5002/api/telegram/save'
    data = {
        'content': content,
        'tags': tags
    }
    
    try:
        r = requests.post(url, json=data, timeout=5)
        if r.status_code == 200:
            print("✅ Saved!")
            return True
        else:
            print(f"❌ Error: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python save_message.py 'Your message' 'tags'")
        sys.exit(1)
    
    content = sys.argv[1]
    tags = sys.argv[2] if len(sys.argv) > 2 else ''
    
    save_message(content, tags)
