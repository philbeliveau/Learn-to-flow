#!/usr/bin/env python3
"""
Database initialization script for Railway deployment
Copies ezbi_analytics.db to the correct location and verifies tables
"""

import os
import shutil
import sqlite3
from pathlib import Path

def init_database():
    """Initialize database for Railway deployment"""
    print("🔧 Initializing EZBI Analytics Database...")
    
    # Source database file (included in repo)
    source_db = Path("data/ezbi_analytics.db")
    
    # Target database location for Railway
    # Try multiple possible locations
    possible_targets = [
        Path("/data/ezbi_analytics.db"),
        Path("./data/ezbi_analytics.db"),
        Path("../data/ezbi_analytics.db"),
        Path("ezbi_analytics.db")
    ]
    
    target_db = possible_targets[0]  # Default to /data/
    
    # Create target directory if needed
    target_db.parent.mkdir(parents=True, exist_ok=True)
    
    if source_db.exists():
        print(f"📊 Copying database from {source_db} to {target_db}")
        shutil.copy2(source_db, target_db)
        
        # Verify database
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"✅ Database initialized with {len(tables)} tables:")
        for table in tables[:5]:  # Show first 5 tables
            print(f"   - {table[0]}")
        
        if len(tables) > 5:
            print(f"   ... and {len(tables) - 5} more tables")
            
        conn.close()
        return True
    else:
        print(f"❌ Source database not found at {source_db}")
        return False

if __name__ == "__main__":
    success = init_database()
    if not success:
        exit(1)
    print("🚀 Database initialization complete!")