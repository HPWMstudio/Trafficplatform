# Ultimate Traffic Platform

**The Autonomous "Detect -> Redirect -> Land" System**

The Ultimate Traffic Platform is a sophisticated, automated system designed to generate, intercept, and redirect online traffic to a target destination. It leverages advanced bot agents, real-time monitoring, and link cloaking technology to maximize click-through rates and user acquisition.

## 🚀 Key Features

*   **Autonomous Traffic Agents**:
    *   **Monitor Agent**: "The Watchtower" - Scans social media and search engines for high-intent keywords.
    *   **Social Agent**: "The Interceptor" - Engages with users via automated replies and cloaked links.
    *   **SEO Agent**: "The Hunter" - Simulates organic search and click behavior to boost rankings.
*   **Advanced Stealth**:
    *   **Fingerprint Spoofing**: Randomizes User-Agent, WebGL, and behavioral patterns to evade anti-bot detection.
    *   **Human Emulation**: Simulates realistic mouse movements, scrolling, and typing.
*   **Smart Redirection**:
    *   **Link Cloaking**: Detects bots and serves them "safe" content (e.g., viral video previews).
    *   **Zero-Latency Redirection**: Instantly redirects real humans to the target landing page.
*   **Unified Control Center**:
    *   **Web Dashboard**: A modern React-based admin panel to manage bots and view live status.
    *   **Master Controller**: A CLI/API backend to orchestrate the entire system.

## 📂 Repository Structure

*   **`MG/` (Mechanism Generation)**: The Python-based backend containing the C2 Server, Agents, and Stealth Core.
*   **`TG/` (Traffic Generation)**: The React/TypeScript frontend containing the Redirection System and Admin Dashboard.
*   **`docs/`**: Comprehensive documentation and guides.

## 📖 Documentation

*   **[Deployment Guide](docs/DEPLOY.md)**: Step-by-step instructions to deploy the system to a VPS and Vercel.
*   **[System Manual & Walkthrough](docs/walkthrough.md)**: A detailed user manual explaining how to operate the platform.
*   **[Implementation Plan](docs/implementation_plan.md)**: The technical roadmap and architecture design.
*   **[Task Tracker](docs/task.md)**: The development checklist and progress log.

## 🛠️ Quick Start

### Prerequisites
*   Docker & Docker Compose
*   Node.js (v18+)

### 1. Run the Backend (MG)
```bash
cd MG
docker-compose up -d
```

### 2. Run the Frontend (TG)
```bash
cd TG
npm install
npm run dev
```

### 3. Access the Dashboard
Visit `http://localhost:5173/admin` to control your botnet.

---
*Disclaimer: This software is for educational and research purposes only. The authors are not responsible for any misuse or violation of Terms of Service.*
