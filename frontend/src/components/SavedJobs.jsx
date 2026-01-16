function SavedJobs({ jobs, onUnsave }) {
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

  return (
    <div className="max-w-4xl mx-auto">
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

              <div className="flex gap-2">
                <button
                  onClick={() => onUnsave(job.id)}
                  className="flex-1 bg-danger text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors font-medium"
                >
                  Remove
                </button>
                <button
                  onClick={() => window.open(`mailto:?subject=Application for ${job.title}`, '_blank')}
                  className="flex-1 bg-primary text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
                >
                  Apply
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default SavedJobs
