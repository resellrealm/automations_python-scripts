import Anthropic from '@anthropic-ai/sdk'
import dotenv from 'dotenv'

dotenv.config()

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
})

export const parseResume = async (resumeText) => {
  try {
    const message = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 2000,
      messages: [{
        role: 'user',
        content: `Parse this resume and extract structured information. Return ONLY valid JSON with this exact structure:
{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "phone number",
  "location": "city, state/country",
  "skills": ["skill1", "skill2", "skill3"],
  "experience": [
    {
      "title": "Job Title",
      "company": "Company Name",
      "duration": "Start - End",
      "description": "Brief description"
    }
  ],
  "education": [
    {
      "degree": "Degree Name",
      "institution": "School Name",
      "year": "Year or Duration"
    }
  ]
}

Resume text:
${resumeText}

Return ONLY the JSON object, no markdown, no explanation.`
      }]
    })

    const content = message.content[0].text

    // Try to extract JSON if it's wrapped in markdown
    let jsonText = content
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      jsonText = jsonMatch[0]
    }

    const parsed = JSON.parse(jsonText)
    return parsed
  } catch (error) {
    console.error('Error parsing resume with AI:', error)
    throw new Error('Failed to parse resume')
  }
}

export const calculateJobMatch = async (userProfile, job) => {
  try {
    const userSkills = Array.isArray(userProfile.skills) ? userProfile.skills : []
    const userExperience = Array.isArray(userProfile.experience) ? userProfile.experience : []
    const userEducation = Array.isArray(userProfile.education) ? userProfile.education : []
    const userLocation = userProfile.location || ''

    const jobRequirements = Array.isArray(job.requirements) ? job.requirements : []

    const message = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 1500,
      messages: [{
        role: 'user',
        content: `You are a job matching AI. Analyze how well this candidate matches this job. Return ONLY valid JSON with this structure:
{
  "matchScore": 85,
  "strengths": ["strength1", "strength2", "strength3"],
  "gaps": ["gap1", "gap2"],
  "summary": "Brief 1-2 sentence summary of the match"
}

matchScore should be 0-100 where:
- 90-100: Excellent match, highly qualified
- 75-89: Strong match, well qualified
- 60-74: Good match, qualified with some gaps
- 40-59: Moderate match, significant gaps
- 0-39: Weak match, many missing requirements

Candidate Profile:
- Skills: ${userSkills.join(', ')}
- Location: ${userLocation}
- Experience: ${userExperience.map(exp => `${exp.title} at ${exp.company}`).join('; ')}
- Education: ${userEducation.map(edu => `${edu.degree} from ${edu.institution}`).join('; ')}

Job Details:
- Title: ${job.title}
- Company: ${job.company}
- Location: ${job.location}
- Type: ${job.jobType}
- Salary: $${job.salary}
- Industry: ${job.industry}
- Description: ${job.description}
- Requirements: ${jobRequirements.join('; ')}

Return ONLY the JSON object, no markdown, no explanation.`
      }]
    })

    const content = message.content[0].text

    // Extract JSON
    let jsonText = content
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      jsonText = jsonMatch[0]
    }

    const result = JSON.parse(jsonText)

    return {
      matchScore: Math.min(100, Math.max(0, result.matchScore)),
      matchReason: {
        strengths: result.strengths || [],
        gaps: result.gaps || [],
        summary: result.summary || ''
      }
    }
  } catch (error) {
    console.error('Error calculating job match:', error)

    // Fallback to basic matching if AI fails
    return {
      matchScore: 50,
      matchReason: {
        strengths: ['Unable to calculate detailed match'],
        gaps: [],
        summary: 'Basic match calculation'
      }
    }
  }
}

export const calculateAllJobMatches = async (userProfile, jobs) => {
  const matches = []

  for (const job of jobs) {
    try {
      const match = await calculateJobMatch(userProfile, job)
      matches.push({
        jobId: job.id,
        ...match
      })
    } catch (error) {
      console.error(`Error matching job ${job.id}:`, error)
      matches.push({
        jobId: job.id,
        matchScore: 50,
        matchReason: {
          strengths: [],
          gaps: [],
          summary: 'Match calculation unavailable'
        }
      })
    }
  }

  return matches
}
