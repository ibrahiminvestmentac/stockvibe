# Deployment Guide: StockVibe AI on Render

This guide outlines the step-by-step process to deploy your **StockVibe AI** application to [Render](https://render.com/).

---

## Step 1: Initialize Git and Push to GitHub

Render deploys code directly from a GitHub repository. Follow these steps to push your project:

1. Open your terminal (PowerShell, Command Prompt, or Git Bash) in your project root directory (`c:\Users\ibrah\OneDrive\Desktop\app`).
2. Initialize git:
   ```bash
   git init
   ```
3. Add all files to the staging area:
   ```bash
   git add .
   ```
4. Commit the files:
   ```bash
   git commit -m "Initial release of StockVibe AI"
   ```
5. Go to [GitHub](https://github.com/), create a new repository called `stockvibe-ai` (keep it private if you want, Render can access private repos once connected).
6. Copy the remote repository URL and link it to your local git:
   ```bash
   git remote add origin <YOUR_GITHUB_REPO_URL>
   git branch -M main
   git push -u origin main
   ```

---

## Step 2: Configure and Deploy on Render

1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** in the top-right corner and select **Web Service**.
3. Connect your GitHub account and select your `stockvibe-ai` repository.
4. Set the following configuration settings:
   - **Name**: `stockvibe-ai`
   - **Region**: Select the one closest to your location.
   - **Branch**: `main`
   - **Runtime**: `Python`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     gunicorn --bind 0.0.0.0:$PORT --chdir backend app:app
     ```

---

## Step 3: Add Environment Variables

Before clicking create, click the **Advanced** button to add environment keys:

1. Click **Add Environment Variable**.
   - **Key**: `GEMINI_API_KEY`
   - **Value**: `AIzaSyC9vVbUhMMMpe1wbtjRKR-fadOuN0dEqe8`
2. Click **Add Environment Variable** again.
   - **Key**: `FLASK_ENV`
   - **Value**: `production`
3. Click **Create Web Service** at the bottom of the page.

Render will start building your service (installing packages and booting Gunicorn) and will provide a live URL (e.g. `https://stockvibe-ai.onrender.com`) where your Stock Analysis Terminal will be hosted!
