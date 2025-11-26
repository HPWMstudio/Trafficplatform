# Deployment Guide: Ultimate Traffic Platform

This guide explains how to deploy the system to a production environment.

## Architecture
-   **Backend (MG)**: Docker Container (Python + Playwright + Redis). Needs a VPS.
-   **Frontend (TG)**: Static Web App. Hosted on Vercel/Netlify.

---

## Part 1: Deploying the Backend (VPS)

You need a VPS (Virtual Private Server) with at least **2GB RAM** (for browser automation).
*Recommended Providers: DigitalOcean, Hetzner, AWS Lightsail.*

1.  **Get a VPS**: Create an Ubuntu 22.04 Droplet/Instance.
2.  **Install Docker**:
    ```bash
    # SSH into your server
    ssh root@your-server-ip

    # Install Docker & Compose
    apt update
    apt install -y docker.io docker-compose
    ```
3.  **Upload Code**:
    Copy the `MG` folder to your server.
    ```bash
    # From your local machine
    scp -r MG root@your-server-ip:/root/MG
    ```
4.  **Start the System**:
    ```bash
    cd /root/MG
    docker-compose up -d --build
    ```
5.  **Verify**:
    Visit `http://your-server-ip:8000/docs`. You should see the C2 API Swagger UI.

---

## Part 2: Deploying the Frontend (Vercel)

1.  **Push to GitHub**:
    Push the `TG` folder to a GitHub repository.
2.  **Import to Vercel**:
    -   Go to Vercel.com -> Add New Project.
    -   Select your repository.
    -   **Root Directory**: Select `TG` (if it's in a subfolder).
3.  **Configure Environment Variables**:
    -   Add a new variable:
        -   **Name**: `VITE_API_URL`
        -   **Value**: `http://your-server-ip:8000/api` (The IP of your VPS from Part 1).
4.  **Deploy**:
    Click "Deploy". Vercel will build the React app and give you a URL (e.g., `https://traffic-platform.vercel.app`).

---

## Part 3: Final Setup

1.  **Access the Dashboard**:
    Go to `https://traffic-platform.vercel.app/admin`.
2.  **Connect**:
    The dashboard should show "C2 SERVER: ONLINE" if your VPS is running.
3.  **Launch Agents**:
    Click "Start Monitor" or "Start Bot Client" from the dashboard.

**Security Note**: Currently, the C2 API is open. For production, you should add an API Key or Basic Auth to `c2_server_v3.py` and `Admin.tsx` to prevent unauthorized control.
