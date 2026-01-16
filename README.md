# Job Swipe - Tinder for Jobs with AI Matching

A modern, full-stack job application with AI-powered matching and a swipe interface. Upload your resume, get intelligent job matches, and swipe right on your dream job. Built with React, Node.js, Express, SQLite, and Claude AI.

## Features

- **AI Resume Parsing**: Upload your resume (PDF/TXT) and AI automatically extracts your skills, experience, and education
- **Intelligent Job Matching**: Claude AI analyzes your profile against each job and calculates match scores (0-100%)
- **Smart Recommendations**: Jobs are automatically sorted by match score, showing you the best opportunities first
- **Match Insights**: See detailed analysis of your strengths and gaps for each position
- **Swipe Interface**: Tinder-style card swipe to like or pass on job listings
- **Job Filters**: Filter jobs by location, job type, salary, and industry
- **Saved Jobs**: View and manage your saved job listings
- **Profile Management**: Edit your information and manage your career profile
- **Full Stack**: Complete application with React frontend and Node.js backend
- **Database**: SQLite database with 25+ sample job listings
- **Responsive Design**: Beautiful UI with Tailwind CSS that works on all devices

## Tech Stack

### Frontend
- React 18
- Vite
- Tailwind CSS
- react-spring (animations)
- react-use-gesture (swipe gestures)

### Backend
- Node.js
- Express
- SQLite (better-sqlite3)
- Claude AI API (Anthropic SDK)
- Multer (file upload)
- PDF-Parse (resume parsing)
- CORS

## Installation

### Prerequisites
- Node.js (v18 or higher)
- npm or yarn
- Anthropic API key (get one at https://console.anthropic.com/)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Tinderbutforjobs
   ```

2. **Install Backend Dependencies**
   ```bash
   cd backend
   npm install
   ```

3. **Install Frontend Dependencies**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Configure API Key**

   Edit `backend/.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_actual_api_key_here
   ```

5. **Seed the Database**
   ```bash
   cd backend
   node src/seed.js
   ```

## Running the Application

You need to run both the backend and frontend servers:

### Start Backend Server

```bash
cd backend
npm start
# Or for development with auto-reload:
npm run dev
```

The backend will run on `http://localhost:5000`

### Start Frontend Development Server

In a new terminal:

```bash
cd frontend
npm run dev
```

The frontend will run on `http://localhost:3000`

### Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

## Usage

### Getting Started with AI Matching

1. **Upload Your Resume**
   - Click "Profile" in the navigation
   - Upload your resume (PDF or TXT format)
   - AI will automatically parse and extract your information

2. **Calculate Job Matches**
   - After uploading your resume, click "Calculate Job Matches"
   - AI will analyze all jobs and generate match scores
   - This takes 1-2 minutes depending on the number of jobs

3. **Start Swiping**
   - Jobs are now sorted by match score (best matches first)
   - Each card shows your match percentage and AI analysis

### Viewing Match Insights

Each job card displays:
- **Match Score**: 0-100% showing how well you fit the role
- **Match Label**: Excellent/Strong/Good/Moderate/Weak Match
- **Your Strengths**: Skills and experience that align with the job
- **Areas to Develop**: Skills or requirements you're missing
- **AI Summary**: Quick overview of the match quality

### Swiping Jobs
1. View the job card with all details (title, company, location, salary, match score)
2. **Swipe right** or click the **♥ button** to save a job
3. **Swipe left** or click the **✕ button** to pass on a job
4. Click the **⚙ button** to adjust filters

### Managing Your Profile
1. Click "Profile" to view/edit your information
2. Upload a new resume to update your profile
3. Edit personal details (name, email, phone, location)
4. View extracted skills, experience, and education
5. Recalculate matches after updating your profile

### Filtering Jobs
1. Click on "Filters" in navigation or the ⚙ button
2. Set your preferences:
   - Location (e.g., "Remote", "New York", "San Francisco")
   - Job Type (Full-time, Part-time, Contract, Internship)
   - Minimum Salary
   - Industry (Technology, Finance, Healthcare, etc.)
3. Click "Apply Filters" to see matching jobs

### Managing Saved Jobs
1. Click "Saved Jobs" in the navigation
2. View all your saved job listings
3. Click "Remove" to unsave a job
4. Click "Apply" to start the application process (opens email)

## API Endpoints

### Jobs
- `GET /api/jobs` - Get all jobs with match scores (supports query params: location, jobType, minSalary, industry)
- `GET /api/jobs/:id` - Get a specific job by ID

### Saved Jobs
- `GET /api/saved-jobs` - Get all saved jobs
- `POST /api/saved-jobs` - Save a job (body: { jobId })
- `DELETE /api/saved-jobs/:id` - Remove a saved job

### Profile & AI
- `GET /api/profile` - Get user profile
- `POST /api/profile` - Create profile (body: profile data)
- `PUT /api/profile` - Update profile (body: updated fields)
- `POST /api/profile/upload-resume` - Upload resume file (multipart/form-data)
- `POST /api/profile/calculate-matches` - Calculate AI match scores for all jobs
- `GET /api/profile/matches` - Get all match scores

### Health Check
- `GET /api/health` - Check if API is running

## Project Structure

```
Tinderbutforjobs/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── SwipeCards.jsx
│   │   │   ├── JobCard.jsx
│   │   │   ├── SavedJobs.jsx
│   │   │   └── Filters.jsx
│   │   ├── styles/
│   │   │   └── index.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── backend/
│   ├── src/
│   │   ├── config/
│   │   │   └── database.js
│   │   ├── models/
│   │   │   └── Job.js
│   │   ├── controllers/
│   │   │   └── jobController.js
│   │   ├── routes/
│   │   │   └── jobRoutes.js
│   │   ├── server.js
│   │   └── seed.js
│   ├── package.json
│   └── .env
└── README.md
```

## Development

### Adding More Jobs

Edit `backend/src/seed.js` and add more job objects to the `sampleJobs` array, then run:

```bash
cd backend
node src/seed.js
```

### Customizing Styles

Edit `frontend/tailwind.config.js` to customize colors and theme:

```javascript
theme: {
  extend: {
    colors: {
      primary: '#6366f1',  // Change primary color
      secondary: '#8b5cf6', // Change secondary color
    }
  }
}
```

### AI Matching System

The app uses Claude AI (Anthropic) for intelligent matching:

**Resume Parsing**
- Extracts structured data from PDF/TXT resumes
- Identifies skills, experience, education automatically
- No manual data entry needed

**Match Score Calculation**
- Analyzes candidate profile against job requirements
- Considers skills, experience, location, education
- Returns 0-100 match score with detailed reasoning
- Identifies strengths and skill gaps

**Match Score Ranges**
- 90-100%: Excellent match, highly qualified
- 75-89%: Strong match, well qualified
- 60-74%: Good match, qualified with some gaps
- 40-59%: Moderate match, significant gaps
- 0-39%: Weak match, many missing requirements

**API Usage**
- Requires Anthropic API key (free tier available)
- Uses Claude 3.5 Sonnet model
- Each resume parse: ~500 tokens
- Each job match: ~800 tokens
- For 25 jobs: ~20,000 tokens total (~$0.06)

### Building for Production

#### Frontend
```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`

#### Backend
The backend is production-ready. Use a process manager like PM2:

```bash
npm install -g pm2
cd backend
pm2 start src/server.js --name job-swipe-api
```

## Troubleshooting

### Port Already in Use
If ports 3000 or 5000 are already in use, you can change them:

**Backend**: Edit `backend/.env`
```
PORT=5001
```

**Frontend**: Edit `frontend/vite.config.js`
```javascript
server: {
  port: 3001
}
```

### Database Issues
If you encounter database errors, delete `backend/database.sqlite` and run the seed script again:

```bash
cd backend
rm database.sqlite
node src/seed.js
```

### AI/API Issues

**"Failed to parse resume" or "Failed to calculate matches"**
- Check that your Anthropic API key is correctly set in `backend/.env`
- Verify your API key is active at https://console.anthropic.com/
- Check backend console for detailed error messages
- Ensure you have API credits available

**Match scores not appearing**
- Make sure you've uploaded a resume first
- Click "Calculate Job Matches" in your profile
- Wait 1-2 minutes for calculation to complete
- Refresh the jobs page

**Resume upload fails**
- Only PDF and TXT files are supported
- File size limit is 5MB
- Check backend logs for parsing errors

## Future Enhancements

- Multi-user support with authentication
- Job application tracking and status updates
- Email notifications for new high-match jobs
- Integration with real job APIs (LinkedIn, Indeed, Glassdoor)
- Cover letter generation with AI
- Interview preparation based on job requirements
- Salary negotiation insights
- Company culture analysis and reviews
- Application deadline reminders
- Job market trend analysis

## License

MIT

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.
