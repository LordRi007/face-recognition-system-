# Free Cloud Deployment Guide for Face Recognition Management System (FRMS)

This guide walks you through deploying your Flask Face Recognition application for **100% free** with **HTTPS (SSL)** enabled (which modern browsers strictly require for live webcam access via `navigator.mediaDevices.getUserMedia()`).

---

## Architecture & Resource Optimizations Completed

Before deploying, we prepared and optimized the project for cloud free tiers:
1. **Lightweight ONNX Runtime**: Configured `onnxruntime` for MobileFaceNet ArcFace (13.6 MB) and UltraFace (1.2 MB). We removed the bulky, unused `deepface` (which pulls ~1.5 GB of TensorFlow/Keras). The container now uses only **~70 MB RAM**—well within free tier limits (512 MB on Render / 16 GB on Hugging Face).
2. **Reverse Proxy & HTTPS Support**: Injected `ProxyFix` into `app/__init__.py` to automatically handle HTTPS headers and SSL termination from cloud load balancers.
3. **Dynamic Port Binding**: Updated `gunicorn.conf.py` to bind to `0.0.0.0:${PORT:-5000}`.
4. **Auto-Seeding**: Configured `run.py` to automatically create database tables and seed default administrator (`admin@frms.local` / `AdminPass123!`) on fresh deployments.
5. **Pre-configured Blueprint**: Created `render.yaml` for 1-click deployment.

---

## Option 1: Render.com (Recommended for Web App)

Render provides free web services with automatic HTTPS (`https://your-app.onrender.com`) and continuous deployment from GitHub.

### Step 1: Push Project to GitHub

1. Open PowerShell in your project folder (`c:\face scan`) and stage your files:
   ```powershell
   git add .
   git commit -m "Prepare FRMS for free cloud deployment"
   ```
2. Create a new repository on GitHub (e.g. `face-recognition-system`).
3. Link and push your repository:
   ```powershell
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/face-recognition-system.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: (Optional but Recommended) Set Up Free Persistent PostgreSQL on Neon.tech

Render's free web service disk is ephemeral (restarts on inactivity). For permanent user and attendance data:
1. Go to [Neon.tech](https://neon.tech) and sign up (100% free tier, 0.5 GB storage).
2. Create a new project (e.g., `frms-db`).
3. Copy the **Connection String** (e.g., `postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require`).

> *Note: If you skip this step, FRMS will automatically default to an SQLite database.*

### Step 3: Deploy on Render

1. Sign up or log into [Render.com](https://render.com) using your GitHub account.
2. Click **New +** > **Web Service**.
3. Select your GitHub repository (`face-recognition-system`).
4. Configure the service settings:
   - **Name**: `face-recognition-system` (or any name you choose)
   - **Region**: Oregon (US West) or Frankfurt (EU)
   - **Runtime**: **Python 3**
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `gunicorn -c gunicorn.conf.py run:app`
   - **Instance Type**: **Free**
5. Under **Environment Variables**, add:
   | Key | Value | Notes |
   |---|---|---|
   | `FLASK_ENV` | `production` | Enables production security configs |
   | `SECRET_KEY` | *(Click "Generate" on Render)* | Used for session signing |
   | `BIOMETRIC_ENCRYPTION_KEY` | `W3dYvGqgV4u2N_VjS4w1n-X98oQ5P6a0M8b4Z2l1Y6A=` | Fernet AES-256 key |
   | `DATABASE_URL` | *(Paste your Neon.tech connection string)* | *(Optional)* |
   | `OPENBLAS_NUM_THREADS` | `1` | Prevents CPU thread exhaustion |
6. Click **Create Web Service**.
7. Render will build the project in ~1-2 minutes and provide your live URL (e.g., `https://face-recognition-system.onrender.com`).

---

## Option 2: Hugging Face Spaces (Best for AI & Vision - 16 GB Free RAM)

Hugging Face Spaces offers **16 GB RAM and 2 vCPUs** for free with instant HTTPS (`https://username-space-name.hf.space`).

### Steps to Deploy:
1. Sign up on [Hugging Face](https://huggingface.co).
2. Go to [New Space](https://huggingface.co/new-space).
3. Fill in the details:
   - **Space Name**: `face-recognition-app`
   - **License**: MIT or Apache 2.0
   - **Space SDK**: Select **Docker** > **Blank**
   - **Visibility**: Public
4. Clone or push your project to the Hugging Face Space repository:
   ```powershell
   git remote add space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/face-recognition-app
   git push space main
   ```
5. Hugging Face will automatically build your `Dockerfile`, launch Gunicorn, and expose your app at `https://<YOUR_HF_USERNAME>-face-recognition-app.hf.space`!

---

## Option 3: Instant Public HTTPS via Cloudflare Tunnel (Zero Cloud Setup)

If you want to test the webcam live from your phone or demo the app to colleagues right now without configuring cloud accounts:

1. Download the free [Cloudflare Tunnel executable (`cloudflared`)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/):
   ```powershell
   winget install Cloudflare.cloudflared
   ```
2. Start your local Flask server:
   ```powershell
   python run.py
   ```
3. In a second terminal window, run:
   ```powershell
   cloudflared tunnel --url http://127.0.0.1:5000
   ```
4. Cloudflare will output a public HTTPS URL like:
   `https://random-words.trycloudflare.com`
5. Open this URL on your phone or laptop. The browser will grant camera permissions over HTTPS!

---

## Default Login Credentials
Once deployed, log in with the pre-seeded accounts:
- **Administrator**: `admin@frms.local` | Password: `AdminPass123!` | PIN: `1234`
- **Staff / Security**: `staff@frms.local` | Password: `StaffPass123!` | PIN: `4321`
- **Demo User**: `alex.chen@frms.local` | Password: `UserPass123!` | PIN: `9876`
