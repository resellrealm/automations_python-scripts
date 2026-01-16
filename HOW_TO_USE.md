# How to Use Your AI-Powered Job Swipe App

## What You Got

A complete, production-ready job application with AI that:
1. **Reads your resume** and understands your skills, experience, and education
2. **Analyzes every job** and tells you exactly how well you match
3. **Ranks jobs** by match score so you see the best opportunities first
4. **Explains the match** showing your strengths and what you're missing
5. **Swipe interface** makes job hunting feel like dating apps

## Getting Started (5 Minutes)

### 1. Get Your FREE API Key

Go to https://console.anthropic.com/ and sign up. You get $5 free credit (enough for analyzing 80+ job sets).

### 2. Add Your API Key

Edit `backend/.env`:
```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

### 3. Start the App

```bash
# In one terminal - Backend
cd backend
npm install
node src/seed.js
npm start

# In another terminal - Frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Using the App

### First Time Setup (2 minutes)

1. **Click "Profile"** in the top navigation
2. **Upload Your Resume** (PDF or TXT)
   - AI will automatically extract everything
   - Your skills, jobs, education - all parsed instantly
3. **Click "Calculate Job Matches"**
   - This takes 1-2 minutes
   - AI is analyzing your fit for every job
   - You'll see a success message when done
4. **Go back to "Swipe"**
   - Jobs are now sorted by how well you match
   - Best matches appear first

### Understanding Match Scores

Each job shows a colored badge with a percentage:

- **90-100% (Green)** - EXCELLENT MATCH
  - You're highly qualified
  - Apply immediately

- **75-89% (Blue)** - STRONG MATCH
  - You're well qualified
  - Good opportunity

- **60-74% (Yellow)** - GOOD MATCH
  - Qualified with some gaps
  - Consider if interested

- **40-59% (Orange)** - MODERATE MATCH
  - Significant gaps
  - Would need development

- **0-39% (Red)** - WEAK MATCH
  - Many missing requirements
  - Probably skip

### Reading the AI Analysis

Each job card shows:

**Your Strengths** (Green)
- Skills and experience you have that match
- Why you're a good fit

**Areas to Develop** (Orange)
- Skills or experience you're missing
- What you'd need to learn/gain

**AI Summary**
- 1-2 sentence overview of the match
- Quick decision-making help

### Daily Workflow

1. Open app → See jobs sorted by match score
2. Read the top card (highest match)
3. Check AI analysis
4. **Swipe Right (♥)** if interested → Saves to "Saved Jobs"
5. **Swipe Left (✕)** if not interested → Moves to next
6. Repeat until you've seen all good matches

### Managing Saved Jobs

1. Click "Saved Jobs" tab
2. See all jobs you swiped right on
3. Click "Apply" to start the application
4. Click "Remove" if you change your mind

### Filtering Jobs

1. Click the ⚙ button or "Filters"
2. Set preferences:
   - **Location**: "Remote", "New York", etc.
   - **Job Type**: Full-time, Part-time, Contract
   - **Minimum Salary**: e.g., 100000
   - **Industry**: Technology, Finance, etc.
3. Click "Apply Filters"
4. Jobs are filtered AND still sorted by match score

### Updating Your Profile

When you gain new skills or experience:
1. Update your resume
2. Go to Profile → Upload new resume
3. Click "Calculate Job Matches" again
4. Match scores update to reflect your new qualifications

## How the AI Works

### Resume Parsing
- AI reads your entire resume
- Extracts structured data (skills, jobs, education)
- No manual data entry needed
- Understands context and formatting

### Job Matching
For each job, AI considers:
- Your skills vs. required skills
- Your experience level and roles
- Your location vs. job location
- Your education vs. requirements
- Job description vs. your background

It then:
- Calculates a 0-100 match score
- Identifies your 3-5 key strengths
- Lists 2-4 gaps you have
- Writes a summary of the match

### Smart Sorting
Jobs are automatically sorted:
1. Highest match score first
2. Helps you focus on best opportunities
3. Don't waste time on poor fits

## Cost & Usage

**Free Tier**: $5 credit (included)
- Parse resume: ~$0.001
- Match 25 jobs: ~$0.06
- You can do ~80 full analyses with free credit

**Paid Usage**: After free credit
- $3 per million input tokens
- $15 per million output tokens
- Roughly $0.06 per 25 job matches

**Tips to Save Money**:
- Parse resume once, match many times
- Only recalculate matches when you update your profile
- Use filters to reduce job count before matching

## Tips for Best Results

### Resume Best Practices
- Include all relevant skills (technical and soft)
- List job titles, companies, and dates clearly
- Add education with degrees and institutions
- Use standard resume formatting
- Keep it detailed but focused (1-2 pages ideal)

### Getting Better Matches
- Be honest about your experience level
- Include certifications and courses
- List tools and technologies you know
- Add measurable achievements
- Update regularly as you gain skills

### Using Match Insights
- **High match + low interest?** Still apply - AI sees potential you might miss
- **Low match + high interest?** Check gaps - decide if learnable
- **Multiple high matches?** Compare AI summaries to prioritize
- **Gaps in multiple jobs?** Consider upskilling in those areas

## Troubleshooting

### "Failed to calculate matches"
- Check your API key in backend/.env
- Ensure you have API credits
- Look at backend console for error details
- Try restarting the backend

### No match scores showing
- Did you upload a resume?
- Did you click "Calculate Job Matches"?
- Did you wait 1-2 minutes?
- Try refreshing the page

### Resume upload fails
- Only PDF and TXT supported
- Max file size: 5MB
- Check if file is corrupted
- Try a different format

### Match scores seem wrong
- AI considers all factors holistically
- Review the detailed analysis
- Check if your resume clearly lists relevant skills
- Try updating resume with more details

## Advanced Usage

### Adding Your Own Jobs

Edit `backend/src/seed.js` and add jobs in this format:

```javascript
{
  title: 'Your Job Title',
  company: 'Company Name',
  location: 'City, State or Remote',
  jobType: 'full-time',
  salary: 100000,
  industry: 'technology',
  description: 'Full job description...',
  requirements: ['Requirement 1', 'Requirement 2']
}
```

Then run:
```bash
cd backend
node src/seed.js
```

### Backing Up Your Data

Your data is in `backend/database.sqlite`:
```bash
cp backend/database.sqlite backup-$(date +%Y%m%d).sqlite
```

### Resetting Everything

```bash
cd backend
rm database.sqlite
node src/seed.js
```

Then re-upload your resume and recalculate matches.

## What Makes This Different

**Traditional Job Boards**:
- You search for keywords
- You guess if you're qualified
- You read every job manually
- No personalization

**This App**:
- AI searches for YOU
- AI tells you if you're qualified (with proof)
- AI pre-filters and ranks everything
- 100% personalized to your actual skills

You spend time applying to good matches, not reading 100 bad ones.

## Next Steps

1. Upload your resume today
2. Calculate matches
3. Save 3-5 jobs you like
4. Apply to your top matches
5. Update weekly as you apply
6. Track your saved jobs

## Support

- Check README.md for technical details
- Check SETUP_GUIDE.md for installation help
- Check backend console for error messages
- API docs: https://docs.anthropic.com/

## Privacy Note

- All data stored locally in SQLite
- Resume stays on your computer
- Only sent to Anthropic API for analysis
- Anthropic doesn't train on your data
- No third-party tracking
- Delete `database.sqlite` to remove all data

---

**You now have a personal AI job hunting assistant. Use it to find your dream job faster!**
