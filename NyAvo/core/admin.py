import sqlite3, json, numpy as np
from integrations.gemini import embed
import structlog

logger = structlog.get_logger()
DB_PATH = "knowledge.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            embedding TEXT
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            old_price REAL,
            promotion TEXT,
            category TEXT,
            brand TEXT,
            stock INTEGER DEFAULT 0,
            available BOOLEAN DEFAULT 1,
            colors TEXT,
            sizes TEXT,
            images TEXT,
            features TEXT,
            similar_products TEXT
        );

        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER,
            product_id INTEGER,
            date TEXT,
            status TEXT,
            carrier TEXT,
            tracking_number TEXT,
            estimated_date TEXT,
            payment_status TEXT
        );

        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            purchase_history TEXT,
            favorite_products TEXT,
            preferences TEXT,
            language TEXT DEFAULT 'fr',
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS promotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            code TEXT UNIQUE,
            discount TEXT,
            start_date TEXT,
            end_date TEXT,
            conditions TEXT
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            order_number TEXT,
            method TEXT,
            status TEXT,
            failure_reason TEXT,
            refund TEXT
        );

        CREATE TABLE IF NOT EXISTS deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            order_number TEXT,
            carrier TEXT,
            status TEXT,
            position TEXT,
            delay BOOLEAN DEFAULT 0,
            estimated_date TEXT
        );

        CREATE TABLE IF NOT EXISTS ai_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            mission TEXT,
            knowledge_base TEXT,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            date TEXT,
            channel TEXT,
            summary TEXT,
            agent_used TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS integrations (
            service TEXT PRIMARY KEY,
            status TEXT DEFAULT 'simulé'
        );
    """)

    # Colonnes manquantes pour compatibilité
    try: conn.execute("ALTER TABLE payments ADD COLUMN order_number TEXT")
    except: pass
    try: conn.execute("ALTER TABLE deliveries ADD COLUMN order_number TEXT")
    except: pass

    conn.commit()
    conn.close()