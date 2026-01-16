import { useState } from 'react'

function SavedJobs({ jobs, onUnsave }) {
  const [expandedJob, setExpandedJob] = useState(null)

  if (jobs.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="bg-white rounded-2xl p-8 shadow-xl text-center max-w-md">
          <div className="text-6xl mb-4">💼</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">No Saved Jobs Yet</h2>
          <p className="text-gray-600">Start swiping to save jobs you're interested in!</p>
        </div>
      </div>
    )
  }

  const handleApply = (job) => {
    if (job.applicationUrl) {
      window.open(job.applicationUrl, '_blank')
    } else if (job.contactEmail) {
      window.open(`mailto:${job.contactEmail}?subject=Application for ${job.title} at ${job.company}`, '_blank')
    } else {
      alert('No application method available for this job.')
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      <h2 className="text-3xl font-bold text-white mb-6">Saved Jobs ({jobs.length})</h2>

      <div className="grid gap-6 md:grid-cols-2">
        {jobs.map(job => (
          <div key={job.id} className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-primary to-secondary p-4 text-white">
              <h3 className="text-xl font-bold">{job.title}</h3>
              <p className="opacity-90">{job.company}</p>
            </div>

            <div className="p-4">
              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 text-gray-700 text-sm">
                  <span>📍</span>
                  <span>{job.location}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-700 text-sm">
                  <span>💼</span>
                  <span className="capitalize">{job.jobType}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-700 text-sm">
                  <span>💰</span>
                  <span className="font-semibold text-success">
                    ${job.salary.toLocaleString()}/year
                  </span>
                </div>
              </div>

              <p className="text-gray-600 text-sm mb-4 line-clamp-3">{job.description}</p>

              {expandedJob === job.id && (
                <div className="mb-4 p-3 bg-gray-50 rounded-lg text-sm space-y-2">
                  {job.applicationUrl && (
                    <div>
                      <span className="font-semibold text-gray-700">Apply Here:</span>{' '}
                      <a
                        href={job.applicationUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline break-all"
                      >
                        {job.applicationUrl}
                      </a>
                    </div>
                  )}
                  {job.companyWebsite && (
                    <div>
                      <span className="font-semibold text-gray-700">Company Website:</span>{' '}
                      <a
                        href={job.companyWebsite}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        {job.companyWebsite}
                      </a>
                    </div>
                  )}
                  {job.contactEmail && (
                    <div>
                      <span className="font-semibold text-gray-700">Contact:</span>{' '}
                      <a
                        href={`mailto:${job.contactEmail}`}
                        className="text-primary hover:underline"
                      >
                        {job.contactEmail}
                      </a>
                    </div>
                  )}
                  {job.applicationNotes && (
                    <div>
                      <span className="font-semibold text-gray-700">Application Notes:</span>{' '}
                      <span className="text-gray-600">{job.applicationNotes}</span>
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-2 mb-2">
                <button
                  onClick={() => setExpandedJob(expandedJob === job.id ? null : job.id)}
                  className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors font-medium text-sm"
                >
                  {expandedJob === job.id ? 'Hide Details' : 'Show Application Info'}
                </button>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => onUnsave(job.id)}
                  className="flex-1 bg-danger text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors font-medium"
                >
                  Remove
                </button>
                <button
                  onClick={() => handleApply(job)}
                  className="flex-1 bg-success text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors font-medium"
                >
                  Apply Now
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-blue-100 border border-blue-300 rounded-lg p-4 text-blue-800">
        <h3 className="font-bold mb-2">💡 Application Tips:</h3>
        <ul className="text-sm space-y-1">
          <li>• Click "Show Application Info" to see application URLs and contact details</li>
          <li>• "Apply Now" opens the application page or email composer</li>
          <li>• Keep notes on when you applied and follow up after 1-2 weeks</li>
          <li>• Tailor your resume/cover letter for each position based on the AI match insights</li>
        </ul>
      </div>
    </div>
  )
}

export default SavedJobs
