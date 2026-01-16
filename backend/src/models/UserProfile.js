import db from '../config/database.js'

export const UserProfile = {
  get: () => {
    const stmt = db.prepare('SELECT * FROM user_profile ORDER BY id DESC LIMIT 1')
    const profile = stmt.get()

    if (profile) {
      if (profile.skills) profile.skills = JSON.parse(profile.skills)
      if (profile.experience) profile.experience = JSON.parse(profile.experience)
      if (profile.education) profile.education = JSON.parse(profile.education)
      if (profile.preferences) profile.preferences = JSON.parse(profile.preferences)
    }

    return profile
  },

  create: (data) => {
    const stmt = db.prepare(`
      INSERT INTO user_profile (name, email, phone, location, resumeText, resumeFileName, skills, experience, education, preferences)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `)

    const result = stmt.run(
      data.name || null,
      data.email || null,
      data.phone || null,
      data.location || null,
      data.resumeText || null,
      data.resumeFileName || null,
      data.skills ? JSON.stringify(data.skills) : null,
      data.experience ? JSON.stringify(data.experience) : null,
      data.education ? JSON.stringify(data.education) : null,
      data.preferences ? JSON.stringify(data.preferences) : null
    )

    return result.lastInsertRowid
  },

  update: (id, data) => {
    const updates = []
    const values = []

    if (data.name !== undefined) {
      updates.push('name = ?')
      values.push(data.name)
    }
    if (data.email !== undefined) {
      updates.push('email = ?')
      values.push(data.email)
    }
    if (data.phone !== undefined) {
      updates.push('phone = ?')
      values.push(data.phone)
    }
    if (data.location !== undefined) {
      updates.push('location = ?')
      values.push(data.location)
    }
    if (data.resumeText !== undefined) {
      updates.push('resumeText = ?')
      values.push(data.resumeText)
    }
    if (data.resumeFileName !== undefined) {
      updates.push('resumeFileName = ?')
      values.push(data.resumeFileName)
    }
    if (data.skills !== undefined) {
      updates.push('skills = ?')
      values.push(JSON.stringify(data.skills))
    }
    if (data.experience !== undefined) {
      updates.push('experience = ?')
      values.push(JSON.stringify(data.experience))
    }
    if (data.education !== undefined) {
      updates.push('education = ?')
      values.push(JSON.stringify(data.education))
    }
    if (data.preferences !== undefined) {
      updates.push('preferences = ?')
      values.push(JSON.stringify(data.preferences))
    }

    updates.push('updatedAt = CURRENT_TIMESTAMP')
    values.push(id)

    const stmt = db.prepare(`UPDATE user_profile SET ${updates.join(', ')} WHERE id = ?`)
    const result = stmt.run(...values)

    return result.changes
  },

  delete: (id) => {
    const stmt = db.prepare('DELETE FROM user_profile WHERE id = ?')
    const result = stmt.run(id)
    return result.changes
  }
}

export const JobMatch = {
  getAll: () => {
    const stmt = db.prepare(`
      SELECT jm.*, j.title, j.company, j.location, j.salary, j.jobType, j.industry
      FROM job_matches jm
      JOIN jobs j ON jm.jobId = j.id
      ORDER BY jm.matchScore DESC
    `)

    const matches = stmt.all()
    return matches.map(match => ({
      ...match,
      matchReason: match.matchReason ? JSON.parse(match.matchReason) : null
    }))
  },

  getByJobId: (jobId) => {
    const stmt = db.prepare('SELECT * FROM job_matches WHERE jobId = ? ORDER BY calculatedAt DESC LIMIT 1')
    const match = stmt.get(jobId)

    if (match && match.matchReason) {
      match.matchReason = JSON.parse(match.matchReason)
    }

    return match
  },

  create: (jobId, matchScore, matchReason) => {
    // Delete old match for this job if exists
    const deleteStmt = db.prepare('DELETE FROM job_matches WHERE jobId = ?')
    deleteStmt.run(jobId)

    // Insert new match
    const stmt = db.prepare(`
      INSERT INTO job_matches (jobId, matchScore, matchReason)
      VALUES (?, ?, ?)
    `)

    const result = stmt.run(
      jobId,
      matchScore,
      matchReason ? JSON.stringify(matchReason) : null
    )

    return result.lastInsertRowid
  },

  deleteAll: () => {
    const stmt = db.prepare('DELETE FROM job_matches')
    const result = stmt.run()
    return result.changes
  }
}
