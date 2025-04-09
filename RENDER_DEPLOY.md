# Detailed Render.com Deployment Guide

This guide provides step-by-step instructions for deploying the Yahoo Finance Stock Scraper to Render.com.

## 1. Create a GitHub Repository

First, upload this codebase to a GitHub repository:

1. Create a new repository on GitHub
2. Upload all the project files (or push from your local Git repository)
3. Make sure to include all .py files, templates, static folders, and configuration files

## 2. Sign Up for Render.com

If you don't have a Render.com account:

1. Go to [render.com](https://render.com/)
2. Sign up for a free account

## 3. Create a New Web Service

1. From your Render dashboard, click "New" and select "Web Service"
2. Choose "Connect a GitHub repository"
3. Grant Render access to your GitHub repositories
4. Select the repository containing the Yahoo Finance scraper
5. Configure your service with the following settings:

### Basic Settings

- **Name**: `yahoo-finance-scraper` (or any name you prefer)
- **Region**: Choose the region closest to your users
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty (uses repository root)
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r render-requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --reuse-port main:app`

### Environment Variables

Click "Advanced" and add the following environment variables:

- `SESSION_SECRET`: Generate a random string or click the "Generate" button
- `FLASK_ENV`: `production`
- `CACHE_TYPE`: `SimpleCache`
- `CACHE_DEFAULT_TIMEOUT`: `1800`
- `LOG_LEVEL`: `INFO`

### Plan Selection

- Select the **Free** plan for testing
- For a production app, consider the **Starter** plan to avoid "spin-down" behavior

## 4. Deploy Your Service

1. Click "Create Web Service"
2. Wait for the build and deployment to complete
3. Once deployed, Render will provide a URL for your application
4. Open the URL to access your Yahoo Finance Stock Scraper

## 5. Troubleshooting Common Issues

### "No Data Found" Error

If you get a "No data found" error when searching for stock data:

1. **Check Ticker Symbol**: Verify you're using the correct ticker (e.g., "MSFT" not "MICROSOFT")
2. **Date Range**: Try limiting your date range to less than 2 years
3. **Server Logs**: Go to your Render dashboard, select your service, and click on "Logs" to see detailed error messages
4. **Free Plan Limitations**: On the free plan, your service will "spin down" after 15 minutes of inactivity, causing the first request after inactivity to be slow

### Other Issues

If you encounter other issues:

1. Check the Render logs for specific error messages
2. Verify all environment variables are set correctly
3. Ensure your render-requirements.txt file includes all necessary dependencies

## 6. Updating Your Application

When you push changes to your GitHub repository, Render will automatically rebuild and deploy your application.

## 7. Custom Domains (Optional)

If you want to use a custom domain instead of the render.app domain:

1. Go to your service settings on Render
2. Click on "Custom Domain"
3. Follow the instructions to add and verify your domain