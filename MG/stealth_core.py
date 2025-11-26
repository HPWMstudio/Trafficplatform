import random
import asyncio
import logging
from typing import Dict, Any, List, Optional
from playwright.async_api import Page, BrowserContext

logger = logging.getLogger(__name__)

class StealthManager:
    """
    Advanced Stealth Manager for bypassing anti-bot protections.
    Handles fingerprint spoofing, human-like behavior, and evasion techniques.
    """

    # --- Fingerprint Data Pools ---
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    VIEWPORTS = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1440, "height": 900},
        {"width": 1536, "height": 864},
    ]

    LOCALES = ["en-US", "en-GB", "de-DE", "fr-FR", "es-ES"]
    TIMEZONES = ["America/New_York", "Europe/London", "Europe/Berlin", "Europe/Paris", "Europe/Madrid"]

    @staticmethod
    def get_stealth_launch_args() -> Dict[str, Any]:
        """
        Returns Playwright launch arguments optimized for stealth.
        """
        return {
            "headless": True, # Can be toggled to False for debugging/visual verification
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-site-isolation-trials",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-infobars",
                "--disable-notifications",
                "--disable-popup-blocking",
                "--ignore-certificate-errors",
                "--disable-gpu", # Sometimes helps, sometimes hurts depending on environment
                "--disable-dev-shm-usage",
            ]
        }

    @staticmethod
    def get_random_context_options() -> Dict[str, Any]:
        """
        Generates a consistent set of browser context options (fingerprint).
        """
        user_agent = random.choice(StealthManager.USER_AGENTS)
        viewport = random.choice(StealthManager.VIEWPORTS)
        locale = random.choice(StealthManager.LOCALES)
        timezone = random.choice(StealthManager.TIMEZONES)
        
        return {
            "user_agent": user_agent,
            "viewport": viewport,
            "locale": locale,
            "timezone_id": timezone,
            "has_touch": False,
            "is_mobile": False,
            "device_scale_factor": 1,
            "color_scheme": "dark" if random.random() > 0.5 else "light",
            "permissions": ["geolocation", "notifications"],
        }

    @staticmethod
    async def apply_stealth_scripts(page: Page):
        """
        Injects JavaScript to mask automation indicators (webdriver, plugins, etc.).
        """
        await page.add_init_script("""
            // 1. Mask WebDriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            // 2. Mock Plugins (Chrome usually has PDF viewer, etc.)
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    var ChromiumPDFPlugin = {};
                    ChromiumPDFPlugin.__proto__ = Plugin.prototype;
                    var plugins = {
                        0: ChromiumPDFPlugin,
                        description: 'Portable Document Format',
                        filename: 'internal-pdf-viewer',
                        length: 1,
                        name: 'Chromium PDF Plugin',
                        __proto__: PluginArray.prototype,
                    };
                    return plugins;
                },
            });

            // 3. Mock Languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });

            // 4. Mock Permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );

            // 5. WebGL Vendor/Renderer Spoofing (Basic)
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    return 'Google Inc. (NVIDIA)';
                }
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)';
                }
                return getParameter(parameter);
            };
        """)
        logger.info("[*] Stealth scripts injected.")

    @staticmethod
    async def simulate_human_behavior(page: Page):
        """
        Performs random mouse movements, scrolls, and pauses to simulate a human.
        """
        try:
            # Random Mouse Movements (Bezier-like curves are hard to do perfectly without a lib, 
            # but we can do random waypoints)
            viewport = page.viewport_size
            if viewport:
                width, height = viewport['width'], viewport['height']
                for _ in range(random.randint(3, 7)):
                    x = random.randint(0, width)
                    y = random.randint(0, height)
                    # Move in steps to simulate speed
                    await page.mouse.move(x, y, steps=random.randint(5, 20))
                    await asyncio.sleep(random.uniform(0.1, 0.5))

            # Random Scrolling
            for _ in range(random.randint(2, 5)):
                scroll_amount = random.randint(100, 800)
                await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                await asyncio.sleep(random.uniform(0.5, 2.0))
                
                # Occasionally scroll up a bit
                if random.random() > 0.7:
                    await page.evaluate(f"window.scrollBy(0, -{random.randint(50, 200)})")
                    await asyncio.sleep(random.uniform(0.5, 1.0))

        except Exception as e:
            logger.warning(f"[!] Error simulating human behavior: {e}")

    @staticmethod
    async def human_type(page: Page, selector: str, text: str):
        """
        Types text into a selector with variable delays between keystrokes.
        """
        try:
            await page.focus(selector)
            for char in text:
                await page.keyboard.type(char)
                # Random delay between keystrokes (30ms to 150ms)
                await asyncio.sleep(random.uniform(0.03, 0.15))
                
                # Occasional long pause (thinking time)
                if random.random() > 0.95:
                    await asyncio.sleep(random.uniform(0.5, 1.2))
        except Exception as e:
            logger.error(f"[-] Error in human_type: {e}")

