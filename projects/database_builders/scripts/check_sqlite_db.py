#!/usr/bin/env python3
"""
Check SQLite Database Contents
"""
import sqlite3
import json

def check_database():
    """Check what's in the SQLite database"""
    
    conn = sqlite3.connect('indian_legal_db.sqlite')
    cursor = conn.cursor()
    
    print("=" * 60)
    print("SQLITE DATABASE ANALYSIS")
    print("=" * 60)
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTables found: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check each table
    for table_name in [t[0] for t in tables]:
        print(f"\n{'='*60}")
        print(f"Table: {table_name}")
        print(f"{'='*60}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Total rows: {count}")
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"\nColumns ({len(columns)}):")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Get sample data
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            
            print(f"\nSample data (first {len(rows)} rows):")
            for i, row in enumerate(rows, 1):
                print(f"\n  Row {i}:")
                for j, col in enumerate(columns):
                    value = row[j]
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"    {col[1]}: {value}")
        
        # Get statistics for legal_documents
        if table_name == "legal_documents":
            print(f"\nStatistics:")
            
            # Count by doc_type
            cursor.execute("SELECT doc_type, COUNT(*) FROM legal_documents GROUP BY doc_type")
            by_type = cursor.fetchall()
            print(f"  By document type:")
            for doc_type, count in by_type:
                print(f"    - {doc_type}: {count}")
            
            # Count by source
            cursor.execute("SELECT source, COUNT(*) FROM legal_documents GROUP BY source")
            by_source = cursor.fetchall()
            print(f"  By source:")
            for source, count in by_source:
                print(f"    - {source}: {count}")
            
            # Date range
            cursor.execute("SELECT MIN(date), MAX(date) FROM legal_documents WHERE date IS NOT NULL AND date != ''")
            date_range = cursor.fetchone()
            if date_range[0]:
                print(f"  Date range: {date_range[0]} to {date_range[1]}")
    
    conn.close()
    print(f"\n{'='*60}")
    print("Database analysis complete")
    print(f"{'='*60}")

if __name__ == "__main__":
    check_database()
