import db from '../config/database.js'

export const Job = {
  getAll: (filters = {}) => {
    let query = 'SELECT * FROM jobs WHERE 1=1'
    const params = []

    if (filters.location) {
      query += ' AND location LIKE ?'
      params.push(`%${filters.location}%`)
    }

    if (filters.jobType) {
      query += ' AND jobType = ?'
      params.push(filters.jobType)
    }

    if (filters.minSalary) {
      query += ' AND salary >= ?'
      params.push(parseInt(filters.minSalary))
    }

    if (filters.industry) {
      query += ' AND industry = ?'
      params.push(filters.industry)
    }

    query += ' ORDER BY RANDOM()'

    const stmt = db.prepare(query)
    const jobs = stmt.all(...params)

    return jobs.map(job => ({
      ...job,
      requirements: job.requirements ? JSON.parse(job.requirements) : []
    }))
  },

  getById: (id) => {
    const stmt = db.prepare('SELECT * FROM jobs WHERE id = ?')
    const job = stmt.get(id)

    if (job && job.requirements) {
      job.requirements = JSON.parse(job.requirements)
    }

    return job
  },

  create: (job) => {
    const stmt = db.prepare(`
      INSERT INTO jobs (title, company, location, jobType, salary, industry, description, requirements)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `)

    const requirements = job.requirements ? JSON.stringify(job.requirements) : null

    const result = stmt.run(
      job.title,
      job.company,
      job.location,
      job.jobType,
      job.salary,
      job.industry,
      job.description,
      requirements
    )

    return result.lastInsertRowid
  }
}

export const SavedJob = {
  getAll: () => {
    const stmt = db.prepare(`
      SELECT j.*, sj.savedAt
      FROM saved_jobs sj
      JOIN jobs j ON sj.jobId = j.id
      ORDER BY sj.savedAt DESC
    `)

    const jobs = stmt.all()

    return jobs.map(job => ({
      ...job,
      requirements: job.requirements ? JSON.parse(job.requirements) : []
    }))
  },

  save: (jobId) => {
    const stmt = db.prepare('INSERT INTO saved_jobs (jobId) VALUES (?)')
    const result = stmt.run(jobId)
    return result.lastInsertRowid
  },

  delete: (jobId) => {
    const stmt = db.prepare('DELETE FROM saved_jobs WHERE jobId = ?')
    const result = stmt.run(jobId)
    return result.changes
  },

  isJobSaved: (jobId) => {
    const stmt = db.prepare('SELECT COUNT(*) as count FROM saved_jobs WHERE jobId = ?')
    const result = stmt.get(jobId)
    return result.count > 0
  }
}
