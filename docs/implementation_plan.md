# Phase 6: Deployment Preparation (Going Online)

## Goal Description
To fulfill the user's request to "deploy it directly online", we will prepare the system for a production environment.
Since the system has two distinct parts (Python Backend with Browser Automation, and React Frontend), we need a split deployment strategy.

## User Review Required
> [!IMPORTANT]
> **Hosting Costs**: While we can configure the code for free deployment (Vercel for Frontend), the **Backend** requires a server capable of running Headless Browsers (Playwright). Free tiers (like Render/Railway) often lack the RAM/CPU for this. A cheap VPS ($5-10/mo) is recommended.

## Proposed Architecture

### 1. Backend: Dockerized Service (MG)
-   **Technology**: Docker & Docker Compose.
-   **Components**:
    -   `c2_server`: The API / Process Manager.
    -   `redis`: The message broker.
    -   `agents`: The actual bots (can be scaled).
-   **Why Docker?**: It bundles Python, Playwright, and all dependencies into a single "Image" that runs anywhere (VPS, Cloud).

### 2. Frontend: Static Web App (TG)
-   **Technology**: Vercel / Netlify.
-   **Configuration**:
    -   Update `App.tsx` / `Admin.tsx` to read `VITE_API_URL` environment variable instead of hardcoded `localhost`.
    -   Add `vercel.json` for routing rules.

## Proposed Changes

### MG (Mechanism Generation)

#### [NEW] [MG/Dockerfile](file:///c:/Users/hp/Downloads/AG/MG/Dockerfile)
-   Base image: `mcr.microsoft.com/playwright/python:v1.40.0-jammy` (Includes browsers).
-   Installs `requirements.txt`.
-   Exposes port 8000.

#### [NEW] [MG/docker-compose.yml](file:///c:/Users/hp/Downloads/AG/MG/docker-compose.yml)
-   Orchestrates `c2_server` and `redis`.

### TG (Traffic Generation)

#### [MODIFY] [TG/Admin.tsx](file:///c:/Users/hp/Downloads/AG/TG/Admin.tsx)
-   Replace `http://localhost:8000` with `import.meta.env.VITE_API_URL`.

#### [NEW] [TG/vercel.json](file:///c:/Users/hp/Downloads/AG/TG/vercel.json)
-   Configures SPA routing (rewrites all to `index.html`).

## Verification Plan

### Manual Verification
1.  **Build Docker**: Run `docker-compose build` locally to ensure the image compiles.
2.  **Frontend Build**: Run `npm run build` in `TG` to ensure production assets are generated.
