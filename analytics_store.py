"""
Analytics interno — sesiones, clicks, descargas de PPT y clicks en tarjetas.
Uso exclusivo del propietario: la ruta /analytics tiene su propia contraseña
(ANALYTICS_PASSWORD), independiente de ACCESS_PASSWORD (la de las 20 personas).

Almacenamiento: SQLite local (analytics.db). Nota de durabilidad importante:
el disco de Render en planes sin "Persistent Disk" es EFÍMERO — los datos se
pierden en cada redeploy o reinicio del servicio. Es suficiente para ver
actividad reciente entre deploys; si se necesita histórico duradero a largo
plazo, hay que agregar un Persistent Disk de Render o mover esto a una BD externa.
"""
import sqlite3, os, json
from contextlib import contextmanager
from datetime import datetime, timedelta

_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_DIR, "analytics.db")


@contextmanager
def _conn():
    c = sqlite3.connect(DB_PATH, timeout=5)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                session_id TEXT,
                event_type TEXT NOT NULL,
                label TEXT,
                meta TEXT,
                ip TEXT,
                ua TEXT
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)")


def log_event(session_id, event_type, label=None, meta=None, ip=None, ua=None):
    with _conn() as c:
        c.execute(
            "INSERT INTO events (ts, session_id, event_type, label, meta, ip, ua) VALUES (?,?,?,?,?,?,?)",
            (
                datetime.utcnow().isoformat(timespec="seconds"),
                session_id,
                event_type,
                (str(label)[:120] if label is not None else None),
                (json.dumps(meta) if isinstance(meta, dict) else None),
                ip,
                (ua or "")[:200],
            ),
        )


def _since(days):
    if days is None:
        return "1=1", []
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat(timespec="seconds")
    return "ts >= ?", [cutoff]


def summary(days=None):
    where, params = _since(days)
    with _conn() as c:
        def _n(sql, extra=()):
            return c.execute(sql, params + list(extra)).fetchone()["n"]
        return {
            "sessions":  _n(f"SELECT COUNT(DISTINCT session_id) n FROM events WHERE {where} AND session_id IS NOT NULL"),
            "logins":    _n(f"SELECT COUNT(*) n FROM events WHERE {where} AND event_type='login'"),
            "pageviews": _n(f"SELECT COUNT(*) n FROM events WHERE {where} AND event_type='pageview'"),
            "downloads": _n(f"SELECT COUNT(*) n FROM events WHERE {where} AND event_type='ppt_download'"),
            "total":     _n(f"SELECT COUNT(*) n FROM events WHERE {where}"),
        }


def top_labels(event_type, days=None, limit=10):
    where, params = _since(days)
    with _conn() as c:
        rows = c.execute(
            f"SELECT label, COUNT(*) n FROM events WHERE {where} AND event_type=? AND label IS NOT NULL "
            f"GROUP BY label ORDER BY n DESC LIMIT ?",
            params + [event_type, limit],
        ).fetchall()
        return [(r["label"], r["n"]) for r in rows]


def event_type_counts(days=None):
    where, params = _since(days)
    with _conn() as c:
        rows = c.execute(
            f"SELECT event_type, COUNT(*) n FROM events WHERE {where} GROUP BY event_type ORDER BY n DESC",
            params,
        ).fetchall()
        return [(r["event_type"], r["n"]) for r in rows]


def daily_sessions(days=14):
    """Sesiones únicas por día — sirve como tendencia de uso."""
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat(timespec="seconds")
    with _conn() as c:
        rows = c.execute(
            "SELECT substr(ts,1,10) d, COUNT(DISTINCT session_id) n FROM events "
            "WHERE ts>=? AND session_id IS NOT NULL GROUP BY d ORDER BY d",
            (cutoff,),
        ).fetchall()
        return [(r["d"], r["n"]) for r in rows]


def recent_events(limit=60):
    with _conn() as c:
        rows = c.execute(
            "SELECT ts, session_id, event_type, label FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
