import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    # Render provides postgres:// but psycopg2 needs postgresql://
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)


def get_connection():
    """Return a new psycopg2 connection."""
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL environment variable is not set')
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_database():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id            SERIAL PRIMARY KEY,
            username      TEXT    UNIQUE NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id            SERIAL PRIMARY KEY,
            user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            file_type     TEXT    NOT NULL CHECK(file_type IN (\'baseline\',\'current\')),
            original_name TEXT    NOT NULL,
            stored_name   TEXT    NOT NULL,
            file_content  TEXT    NOT NULL,
            file_size     INTEGER NOT NULL,
            uploaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drift_reports (
            id                  SERIAL PRIMARY KEY,
            user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            report_name         TEXT    NOT NULL,
            overall_drift_score REAL    NOT NULL,
            drift_status        TEXT    NOT NULL,
            baseline_files      TEXT    NOT NULL,
            current_files       TEXT    NOT NULL,
            total_features      INTEGER NOT NULL,
            drifted_features    INTEGER NOT NULL,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drift_features (
            id             SERIAL PRIMARY KEY,
            report_id      INTEGER NOT NULL REFERENCES drift_reports(id) ON DELETE CASCADE,
            feature_name   TEXT    NOT NULL,
            psi_score      REAL,
            kl_divergence  REAL,
            js_divergence  REAL,
            ks_statistic   REAL,
            ks_pvalue      REAL,
            drift_status   TEXT    NOT NULL,
            baseline_mean  REAL,
            current_mean   REAL,
            baseline_std   REAL,
            current_std    REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lifespan_predictions (
            id                       SERIAL PRIMARY KEY,
            report_id                INTEGER NOT NULL UNIQUE REFERENCES drift_reports(id) ON DELETE CASCADE,
            health_score             REAL    NOT NULL,
            health_label             TEXT    NOT NULL,
            health_percentage        REAL    NOT NULL,
            days_remaining           INTEGER NOT NULL,
            recommended_retrain_date TEXT    NOT NULL,
            confidence               REAL    NOT NULL,
            velocity                 REAL    NOT NULL,
            velocity_label           TEXT    NOT NULL,
            trend_direction          TEXT,
            trend_json               TEXT,
            risk_factors_json        TEXT,
            feature_insights_json    TEXT,
            recommendation           TEXT,
            predicted_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print('Database initialised (PostgreSQL)')


if __name__ == '__main__':
    init_database()
