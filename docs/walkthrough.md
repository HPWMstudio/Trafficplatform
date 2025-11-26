# The Ultimate Traffic Platform: System Manual

## 1. System Philosophy: "Detect -> Redirect -> Land"
This platform is designed to be an autonomous traffic generation engine. It operates on a simple but powerful 3-step mechanism:

1.  **DETECT**: The **Monitor Agent** patrols the internet (Social Media, Search Engines) to find users expressing intent (e.g., "I need X").
2.  **REDIRECT**: The **Social/SEO Agents** intercept these users with **Cloaked Links**. These links look like trusted content (Viral Videos, News) to bots, but are instant portals for humans.
3.  **LAND**: The **Redirection System** instantly drops the user onto your target destination with Zero-UI latency.

## 2. Component Overview

### The Master Controller (`MG/master_controller.py`)
The central command dashboard. Use this to launch and manage all other components.

### The Agents (Mechanism Generation)
-   **Monitor Agent** (`monitor_agent.py`): The Watchtower. Scans for keywords.
-   **Social Agent** (`social_agent.py`): The Interceptor. Logs in and posts comments/replies.
-   **SEO Agent** (`seo_agent.py`): The Hunter. Boosts organic ranking via "Search & Click".
-   **Stealth Core** (`stealth_core.py`): The Cloak. Spoofs fingerprints to bypass anti-bot protections.

### The Infrastructure (Traffic Generation)
-   **C2 Server** (`c2_server_v3.py`): The Brain. Issues commands to the botnet.
-   **Redirection Page** (`Redirect.tsx`): The Trap. Implements Link Cloaking and Zero-Latency redirects.

## 3. Operation Guide

### Step 1: Start the Platform
Run the Master Controller:
```bash
python MG/master_controller.py
```

### Step 2: Launch Components
From the Master Controller menu:
1.  **Start C2 Server**: Initializes the command center.
2.  **Start Monitor Agent**: Begins scanning for traffic opportunities.
3.  **Start Bot Client**: Connects your bots (or local test bot) to the C2.

### Step 3: Issue Commands (Manual Mode)
If you want to manually direct traffic, use the C2 API (or a future UI) to send commands:

**Social Interception:**
```json
{
  "action": "SOCIAL",
  "sub_action": "INTERACT",
  "target_url": "https://twitter.com/user/status/123",
  "content": "Check this out: http://my-redirect.com"
}
```

**SEO Boost:**
```json
{
  "action": "SEO",
  "engine": "google",
  "keyword": "best traffic tool",
  "target_domain": "my-redirect.com"
}
```

## 4. Advanced Features

### Link Cloaking
The system automatically detects bots (Twitterbot, FacebookBot, etc.).
-   **Bots see**: A "Viral Video" preview card (high CTR).
-   **Humans see**: Nothing. They are instantly redirected.

### Stealth Mode
All agents use `StealthManager` to randomize:
-   User-Agent
-   Screen Resolution
-   Timezone/Locale
-   WebGL Fingerprints
-   Typing Speed & Mouse Movement

## 5. Disclaimer
The system will now autonomously patrol for traffic opportunities and intercept them with high-conversion cloaked links.

## Phase 5: Web Dashboard (The Control Center)

We have replaced the CLI with a modern **Web-Based Control Center**.

### Features
-   **Visual Status**: See instantly which agents are running.
-   **One-Click Control**: Start/Stop the Monitor, Bots, and SEO Agents from the UI.
-   **Task Builder**: Send `SOCIAL` and `SEO` commands using a simple form.

### How to Access
1.  Start the C2 Server: `python MG/c2_server_v3.py`
2.  Start the Frontend: `npm run dev` (in `TG` directory)
3.  Navigate to: `http://localhost:5173/admin`

You now have full control over the Ultimate Traffic Platform from a single, beautiful interface.

## 6. Disclaimer
Use responsibly and ensure you comply with all relevant terms of service and laws regarding automated interaction and traffic redirection.
