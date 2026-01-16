# Job Swipe - Tinder for Jobs

A modern, full-stack job application with a swipe interface. Swipe right to save jobs you like, swipe left to pass. Built with React, Node.js, Express, and SQLite.

## Features

- **Swipe Interface**: Tinder-style card swipe to like or pass on job listings
- **Job Filters**: Filter jobs by location, job type, salary, and industry
- **Saved Jobs**: View and manage your saved job listings
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
- CORS

## Installation

### Prerequisites
- Node.js (v18 or higher)
- npm or yarn

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

4. **Seed the Database**
   ```bash
   cd ../backend
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

### Swiping Jobs
1. View the job card with all details (title, company, location, salary, etc.)
2. **Swipe right** or click the **♥ button** to save a job
3. **Swipe left** or click the **✕ button** to pass on a job
4. Click the **⚙ button** to adjust filters

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
- `GET /api/jobs` - Get all jobs (supports query params: location, jobType, minSalary, industry)
- `GET /api/jobs/:id` - Get a specific job by ID

### Saved Jobs
- `GET /api/saved-jobs` - Get all saved jobs
- `POST /api/saved-jobs` - Save a job (body: { jobId })
- `DELETE /api/saved-jobs/:id` - Remove a saved job

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

## Future Enhancements

- User authentication and profiles
- Job application tracking
- Email notifications for new jobs
- Integration with real job APIs (LinkedIn, Indeed)
- Advanced matching algorithm
- Resume upload and parsing
- Company profiles and reviews

## License

MIT

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.
