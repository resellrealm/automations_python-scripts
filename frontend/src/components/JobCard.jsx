function JobCard({ job }) {
  const getMatchColor = (score) => {
    if (score >= 90) return 'bg-green-500'
    if (score >= 75) return 'bg-blue-500'
    if (score >= 60) return 'bg-yellow-500'
    if (score >= 40) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const getMatchLabel = (score) => {
    if (score >= 90) return 'Excellent Match'
    if (score >= 75) return 'Strong Match'
    if (score >= 60) return 'Good Match'
    if (score >= 40) return 'Moderate Match'
    return 'Weak Match'
  }

  return (
    <div className="bg-white rounded-2xl shadow-2xl h-full overflow-hidden flex flex-col">
      <div className="bg-gradient-to-r from-primary to-secondary p-6 text-white relative">
        {job.matchScore !== null && job.matchScore !== undefined && (
          <div className="absolute top-4 right-4 flex flex-col items-center">
            <div className={`${getMatchColor(job.matchScore)} text-white px-4 py-2 rounded-full font-bold text-lg shadow-lg`}>
              {job.matchScore}%
            </div>
            <span className="text-xs mt-1 opacity-90">{getMatchLabel(job.matchScore)}</span>
          </div>
        )}
        <h2 className="text-2xl font-bold mb-2 pr-24">{job.title}</h2>
        <p className="text-lg opacity-90">{job.company}</p>
      </div>

      <div className="flex-1 p-6 overflow-y-auto">
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-gray-700">
            <span className="text-xl">📍</span>
            <span>{job.location}</span>
          </div>

          <div className="flex items-center gap-2 text-gray-700">
            <span className="text-xl">💼</span>
            <span className="capitalize">{job.jobType}</span>
          </div>

          <div className="flex items-center gap-2 text-gray-700">
            <span className="text-xl">💰</span>
            <span className="font-semibold text-success">
              ${job.salary.toLocaleString()}/year
            </span>
          </div>

          <div className="flex items-center gap-2 text-gray-700">
            <span className="text-xl">🏢</span>
            <span className="capitalize">{job.industry}</span>
          </div>

          <div className="pt-4 border-t">
            <h3 className="font-semibold text-gray-800 mb-2">Description</h3>
            <p className="text-gray-600 leading-relaxed">{job.description}</p>
          </div>

          {job.requirements && job.requirements.length > 0 && (
            <div className="pt-4 border-t">
              <h3 className="font-semibold text-gray-800 mb-2">Requirements</h3>
              <ul className="list-disc list-inside text-gray-600 space-y-1">
                {job.requirements.map((req, index) => (
                  <li key={index}>{req}</li>
                ))}
              </ul>
            </div>
          )}

          {job.matchReason && (
            <div className="pt-4 border-t">
              <h3 className="font-semibold text-gray-800 mb-2">AI Match Analysis</h3>
              {job.matchReason.summary && (
                <p className="text-gray-600 mb-3 text-sm italic">{job.matchReason.summary}</p>
              )}
              {job.matchReason.strengths && job.matchReason.strengths.length > 0 && (
                <div className="mb-2">
                  <h4 className="text-sm font-medium text-green-700 mb-1">Your Strengths:</h4>
                  <ul className="list-disc list-inside text-sm text-gray-600">
                    {job.matchReason.strengths.map((strength, index) => (
                      <li key={index}>{strength}</li>
                    ))}
                  </ul>
                </div>
              )}
              {job.matchReason.gaps && job.matchReason.gaps.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-orange-700 mb-1">Areas to Develop:</h4>
                  <ul className="list-disc list-inside text-sm text-gray-600">
                    {job.matchReason.gaps.map((gap, index) => (
                      <li key={index}>{gap}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default JobCard
