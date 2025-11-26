import asyncio
import os
from bot_client_v3 import AdvancedBotClient

async def test_interaction():
    print("[*] Starting Bot Interaction Verification...")
    
    # Path to local test file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Adjust path to where test_form.html is located relative to this script
    # Assuming this script is in MG folder where bot_client_v3 is
    test_file_path = os.path.join(os.path.dirname(base_dir), "test_form.html")
    
    if not os.path.exists(test_file_path):
        # Try absolute path if relative fails or if script is run from different location
        test_file_path = r"c:\Users\hp\Downloads\AG\test_form.html"
    
    target_url = f"file:///{test_file_path.replace(os.sep, '/')}"
    print(f"[*] Target URL: {target_url}")

    async with AdvancedBotClient() as bot:
        await bot.initialize_browser()
        
        print("[*] Test 1: Visiting Page")
        success = await bot.execute_command({
            "action": "VISIT",
            "target_url": target_url,
            "dwell_time": 2
        })
        if not success:
            print("[-] Visit failed!")
            return

        print("[*] Test 2: Typing Username")
        success = await bot.execute_command({
            "action": "TYPE",
            "target_url": target_url,
            "selector": "#username",
            "text": "TestBot_01"
        })
        if not success:
            print("[-] Type Username failed!")
            return

        print("[*] Test 3: Typing Comment")
        success = await bot.execute_command({
            "action": "TYPE",
            "target_url": target_url,
            "selector": "#comment",
            "text": "This is a verified automated post."
        })
        if not success:
            print("[-] Type Comment failed!")
            return

        print("[*] Test 4: Clicking Submit")
        success = await bot.execute_command({
            "action": "CLICK",
            "target_url": target_url,
            "selector": "#submitBtn"
        })
        if not success:
            print("[-] Click Submit failed!")
            return

        print("[+] Verification Successful! Bot performed all actions.")
        # Keep browser open briefly to see result if watching (headless is true though)
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_interaction())
