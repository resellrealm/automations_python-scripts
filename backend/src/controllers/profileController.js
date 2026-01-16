import { UserProfile, JobMatch } from '../models/UserProfile.js'
import { Job } from '../models/Job.js'
import { parseResume, calculateJobMatch, calculateAllJobMatches } from '../services/aiService.js'
import multer from 'multer'
import pdfParse from 'pdf-parse'
import fs from 'fs'

// Configure multer for file upload
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = './uploads'
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true })
    }
    cb(null, uploadDir)
  },
  filename: (req, file, cb) => {
    cb(null, `resume-${Date.now()}-${file.originalname}`)
  }
})

export const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'application/pdf' || file.mimetype === 'text/plain') {
      cb(null, true)
    } else {
      cb(new Error('Only PDF and TXT files are allowed'))
    }
  },
  limits: { fileSize: 5 * 1024 * 1024 } // 5MB limit
})

export const getProfile = (req, res) => {
  try {
    const profile = UserProfile.get()

    if (!profile) {
      return res.status(404).json({ error: 'Profile not found' })
    }

    res.json(profile)
  } catch (error) {
    console.error('Error fetching profile:', error)
    res.status(500).json({ error: 'Failed to fetch profile' })
  }
}

export const createProfile = async (req, res) => {
  try {
    const data = req.body

    const profileId = UserProfile.create(data)

    res.status(201).json({
      id: profileId,
      message: 'Profile created successfully'
    })
  } catch (error) {
    console.error('Error creating profile:', error)
    res.status(500).json({ error: 'Failed to create profile' })
  }
}

export const updateProfile = async (req, res) => {
  try {
    const profile = UserProfile.get()

    if (!profile) {
      return res.status(404).json({ error: 'Profile not found' })
    }

    const changes = UserProfile.update(profile.id, req.body)

    if (changes === 0) {
      return res.status(404).json({ error: 'Profile not found' })
    }

    res.json({ message: 'Profile updated successfully' })
  } catch (error) {
    console.error('Error updating profile:', error)
    res.status(500).json({ error: 'Failed to update profile' })
  }
}

export const uploadResume = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' })
    }

    let resumeText = ''

    // Extract text from PDF or TXT
    if (req.file.mimetype === 'application/pdf') {
      const dataBuffer = fs.readFileSync(req.file.path)
      const pdfData = await pdfParse(dataBuffer)
      resumeText = pdfData.text
    } else {
      resumeText = fs.readFileSync(req.file.path, 'utf8')
    }

    // Parse resume with AI
    console.log('Parsing resume with AI...')
    const parsedData = await parseResume(resumeText)

    // Create or update profile
    let profile = UserProfile.get()

    const profileData = {
      name: parsedData.name,
      email: parsedData.email,
      phone: parsedData.phone,
      location: parsedData.location,
      resumeText: resumeText,
      resumeFileName: req.file.originalname,
      skills: parsedData.skills,
      experience: parsedData.experience,
      education: parsedData.education
    }

    if (profile) {
      UserProfile.update(profile.id, profileData)
    } else {
      UserProfile.create(profileData)
    }

    // Clean up uploaded file
    fs.unlinkSync(req.file.path)

    res.json({
      message: 'Resume uploaded and parsed successfully',
      data: parsedData
    })
  } catch (error) {
    console.error('Error uploading resume:', error)

    // Clean up file if it exists
    if (req.file && fs.existsSync(req.file.path)) {
      fs.unlinkSync(req.file.path)
    }

    res.status(500).json({
      error: 'Failed to process resume',
      details: error.message
    })
  }
}

export const calculateMatches = async (req, res) => {
  try {
    const profile = UserProfile.get()

    if (!profile) {
      return res.status(400).json({ error: 'Please create a profile first' })
    }

    console.log('Fetching jobs...')
    const jobs = Job.getAll()

    if (jobs.length === 0) {
      return res.json({ message: 'No jobs to match', matches: [] })
    }

    console.log(`Calculating matches for ${jobs.length} jobs...`)

    // Clear old matches
    JobMatch.deleteAll()

    // Calculate new matches
    const matches = await calculateAllJobMatches(profile, jobs)

    // Save matches to database
    for (const match of matches) {
      JobMatch.create(match.jobId, match.matchScore, match.matchReason)
    }

    console.log('Matches calculated and saved')

    res.json({
      message: 'Job matches calculated successfully',
      matchCount: matches.length
    })
  } catch (error) {
    console.error('Error calculating matches:', error)
    res.status(500).json({
      error: 'Failed to calculate job matches',
      details: error.message
    })
  }
}

export const getMatches = (req, res) => {
  try {
    const matches = JobMatch.getAll()
    res.json(matches)
  } catch (error) {
    console.error('Error fetching matches:', error)
    res.status(500).json({ error: 'Failed to fetch matches' })
  }
}
