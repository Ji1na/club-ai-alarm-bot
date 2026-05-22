import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "alimi.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT NOT NULL,
            date         TEXT NOT NULL,
            time         TEXT NOT NULL,
            location     TEXT NOT NULL,
            material_url TEXT,
            created_at   TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id  TEXT NOT NULL,
            member_name TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            arrived_at TEXT NOT NULL,
            is_late    INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ DB 초기화 완료")


# ── 세션 ──────────────────────────────────────────────────
def save_session(title, date, time_, location, material_url=None) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO sessions (title, date, time, location, material_url) VALUES (?,?,?,?,?)",
        (title, date, time_, location, material_url)
    )
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    return session_id


def get_session(session_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_sessions() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM sessions ORDER BY date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── 출석 ──────────────────────────────────────────────────
def record_attendance(member_id, member_name, session_id, arrived_at, is_late: bool):
    conn = get_conn()
    conn.execute(
        "INSERT INTO attendance (member_id, member_name, session_id, arrived_at, is_late) VALUES (?,?,?,?,?)",
        (str(member_id), member_name, session_id, arrived_at, int(is_late))
    )
    conn.commit()
    conn.close()


# ── 지각 통계 ─────────────────────────────────────────────
def get_late_ranking() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT member_name AS name, COUNT(*) AS late_count
        FROM attendance
        WHERE is_late = 1
        GROUP BY member_id
        ORDER BY late_count DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_late_members(threshold: int = 3) -> list[dict]:
    """지각 횟수가 threshold 이상인 멤버 반환"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT member_name AS name, COUNT(*) AS late_count
        FROM attendance
        WHERE is_late = 1
        GROUP BY member_id
        HAVING late_count >= ?
        ORDER BY late_count DESC
    """, (threshold,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
