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
      INSERT INTO jobs (title, company, location, jobType, salary, industry, description, requirements, applicationUrl, companyWebsite, contactEmail, applicationNotes)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
      requirements,
      job.applicationUrl || null,
      job.companyWebsite || null,
      job.contactEmail || null,
      job.applicationNotes || null
    )

    return result.lastInsertRowid
  }
}

export const JobApplication = {
  getAll: () => {
    const stmt = db.prepare(`
      SELECT ja.*, j.title, j.company, j.location, j.salary, j.jobType, j.applicationUrl, j.contactEmail
      FROM job_applications ja
      JOIN jobs j ON ja.jobId = j.id
      ORDER BY ja.updatedAt DESC
    `)
    const apps = stmt.all()
    return apps
  },

  getByJobId: (jobId) => {
    const stmt = db.prepare('SELECT * FROM job_applications WHERE jobId = ? ORDER BY updatedAt DESC LIMIT 1')
    return stmt.get(jobId)
  },

  create: (jobId, data = {}) => {
    const stmt = db.prepare(`
      INSERT INTO job_applications (jobId, status, notes, coverLetter)
      VALUES (?, ?, ?, ?)
    `)
    const result = stmt.run(
      jobId,
      data.status || 'saved',
      data.notes || null,
      data.coverLetter || null
    )
    return result.lastInsertRowid
  },

  update: (id, data) => {
    const updates = []
    const values = []

    if (data.status) {
      updates.push('status = ?')
      values.push(data.status)
    }
    if (data.appliedAt) {
      updates.push('appliedAt = ?')
      values.push(data.appliedAt)
    }
    if (data.notes !== undefined) {
      updates.push('notes = ?')
      values.push(data.notes)
    }
    if (data.coverLetter !== undefined) {
      updates.push('coverLetter = ?')
      values.push(data.coverLetter)
    }

    updates.push('updatedAt = CURRENT_TIMESTAMP')
    values.push(id)

    const stmt = db.prepare(`UPDATE job_applications SET ${updates.join(', ')} WHERE id = ?`)
    const result = stmt.run(...values)
    return result.changes
  },

  markApplied: (jobId) => {
    const existing = JobApplication.getByJobId(jobId)
    if (existing) {
      return JobApplication.update(existing.id, {
        status: 'applied',
        appliedAt: new Date().toISOString()
      })
    } else {
      return JobApplication.create(jobId, {
        status: 'applied',
        appliedAt: new Date().toISOString()
      })
    }
  },

  delete: (id) => {
    const stmt = db.prepare('DELETE FROM job_applications WHERE id = ?')
    const result = stmt.run(id)
    return result.changes
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
