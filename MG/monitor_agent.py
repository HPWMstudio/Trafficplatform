import asyncio
import logging
import random
import re
from typing import List, Dict, Any
from bot_client_v3 import AdvancedBotClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [MONITOR] - %(message)s')
logger = logging.getLogger(__name__)

class MonitorAgent:
    """
    The Watchtower: Monitors streams for keywords and triggers interception.
    """

    def __init__(self, keywords: List[str], target_redirect_url: str):
        self.keywords = keywords
        self.target_redirect_url = target_redirect_url
        self.processed_posts = set()

    async def start_monitoring(self):
        """
        Main monitoring loop.
        """
        logger.info(f"[*] Starting Monitor for keywords: {self.keywords}")
        
        async with AdvancedBotClient() as bot:
            await bot.initialize_browser()
            
            while True:
                try:
                    # 1. Poll for new posts (Simulated)
                    new_posts = await self._fetch_simulated_feed()
                    
                    for post in new_posts:
                        if post['id'] in self.processed_posts:
                            continue
                            
                        # 2. Analyze for Intent
                        if self._analyze_intent(post['content']):
                            logger.info(f"[!] INTENT DETECTED in post {post['id']}: '{post['content']}'")
                            
                            # 3. Trigger Interception (Reply with Cloaked Link)
                            await self._intercept(bot, post)
                            
                        self.processed_posts.add(post['id'])
                    
                    await asyncio.sleep(5) # Poll interval
                    
                except Exception as e:
                    logger.error(f"[-] Monitor error: {e}")
                    await asyncio.sleep(5)

    async def _fetch_simulated_feed(self) -> List[Dict[str, Any]]:
        """
        Simulates fetching a social feed.
        """
        # In a real scenario, this would scrape a URL or hit an API.
        # Here we generate random posts, occasionally with keywords.
        
        templates = [
            "Just had a great lunch.",
            "Anyone know where to find cheap shoes?",
            "Looking for a good movie recommendation.",
            "I need a new laptop, any suggestions?",
            "Beautiful weather today!",
            "I want to buy a crypto wallet.",
        ]
        
        posts = []
        # 30% chance to generate a new post
        if random.random() > 0.7:
            content = random.choice(templates)
            post_id = str(random.randint(1000, 9999))
            posts.append({
                "id": post_id,
                "content": content,
                "platform": "twitter", # Simulated
                "url": "https://twitter.com/simulated/status/" + post_id # Fake URL
            })
            
        return posts

    def _analyze_intent(self, content: str) -> bool:
        """
        Checks if content matches target keywords.
        """
        for keyword in self.keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', content, re.IGNORECASE):
                return True
        return False

    async def _intercept(self, bot: AdvancedBotClient, post: Dict[str, Any]):
        """
        Triggers the bot to reply with the cloaked link.
        """
        # Construct the reply
        cloaked_link = self.target_redirect_url
        reply_content = f"I found exactly what you need here: {cloaked_link}"
        
        logger.info(f"[*] Intercepting Post {post['id']} with link: {cloaked_link}")
        
        # In a real system, we would use bot.execute_social_command()
        # For this simulation, we'll just log the "Action"
        
        # Simulate the bot action delay
        await asyncio.sleep(random.uniform(2, 5))
        logger.info(f"[+] INTERCEPTION SUCCESSFUL: Replied to {post['id']}")

if __name__ == "__main__":
    # Configuration
    KEYWORDS = ["need", "want", "looking for", "buy", "recommendation"]
    TARGET_URL = "http://localhost:5000/redirect?cloaked=true" # The TG Redirection URL
    
    agent = MonitorAgent(KEYWORDS, TARGET_URL)
    asyncio.run(agent.start_monitoring())
