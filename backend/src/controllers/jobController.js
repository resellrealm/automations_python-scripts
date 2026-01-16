import { Job, SavedJob } from '../models/Job.js'

export const getJobs = (req, res) => {
  try {
    const filters = {
      location: req.query.location,
      jobType: req.query.jobType,
      minSalary: req.query.minSalary,
      industry: req.query.industry
    }

    const jobs = Job.getAll(filters)
    res.json(jobs)
  } catch (error) {
    console.error('Error fetching jobs:', error)
    res.status(500).json({ error: 'Failed to fetch jobs' })
  }
}

export const getJobById = (req, res) => {
  try {
    const job = Job.getById(req.params.id)

    if (!job) {
      return res.status(404).json({ error: 'Job not found' })
    }

    res.json(job)
  } catch (error) {
    console.error('Error fetching job:', error)
    res.status(500).json({ error: 'Failed to fetch job' })
  }
}

export const getSavedJobs = (req, res) => {
  try {
    const savedJobs = SavedJob.getAll()
    res.json(savedJobs)
  } catch (error) {
    console.error('Error fetching saved jobs:', error)
    res.status(500).json({ error: 'Failed to fetch saved jobs' })
  }
}

export const saveJob = (req, res) => {
  try {
    const { jobId } = req.body

    if (!jobId) {
      return res.status(400).json({ error: 'Job ID is required' })
    }

    const job = Job.getById(jobId)
    if (!job) {
      return res.status(404).json({ error: 'Job not found' })
    }

    if (SavedJob.isJobSaved(jobId)) {
      return res.status(400).json({ error: 'Job already saved' })
    }

    const savedId = SavedJob.save(jobId)
    res.status(201).json({ id: savedId, message: 'Job saved successfully' })
  } catch (error) {
    console.error('Error saving job:', error)
    res.status(500).json({ error: 'Failed to save job' })
  }
}

export const unsaveJob = (req, res) => {
  try {
    const jobId = parseInt(req.params.id)

    const changes = SavedJob.delete(jobId)

    if (changes === 0) {
      return res.status(404).json({ error: 'Saved job not found' })
    }

    res.json({ message: 'Job removed from saved list' })
  } catch (error) {
    console.error('Error unsaving job:', error)
    res.status(500).json({ error: 'Failed to unsave job' })
  }
}
