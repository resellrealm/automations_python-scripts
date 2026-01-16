# Quick Setup Guide

## Step 1: Get Your Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (you won't be able to see it again)

## Step 2: Configure the Application

Edit `backend/.env` and replace the placeholder:

```
PORT=5000
DATABASE_PATH=./database.sqlite
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx  # Replace with your actual key
```

## Step 3: Install and Run

### Option 1: Quick Start (Recommended)

```bash
./start.sh
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
npm install
node src/seed.js
npm start
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Step 4: Use the App

1. Open http://localhost:3000
2. Click "Profile" in the navigation
3. Upload your resume (PDF or TXT)
4. Click "Calculate Job Matches"
5. Wait 1-2 minutes for AI to analyze all jobs
6. Start swiping!

## Quick Tips

- **First Time**: Upload resume → Calculate matches → Browse jobs
- **Best Results**: Keep your resume updated and detailed
- **Match Scores**: Green (90+) = Excellent, Blue (75+) = Strong, Yellow (60+) = Good
- **Filtering**: Use filters to narrow down by location, salary, or industry
- **Saved Jobs**: Swipe right on jobs you like, view them in "Saved Jobs"

## Cost Estimate

With the free Anthropic tier:
- Resume parsing: ~$0.001 per resume
- Job matching: ~$0.002 per job
- For 25 jobs: ~$0.06 total
- Free tier includes $5 credit (enough for ~80 full analyses)

## Need Help?

Check the main README.md for:
- Detailed API documentation
- Troubleshooting guide
- Advanced configuration options
- Development instructions
