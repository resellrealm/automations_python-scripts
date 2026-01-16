function JobCard({ job }) {
  return (
    <div className="bg-white rounded-2xl shadow-2xl h-full overflow-hidden flex flex-col">
      <div className="bg-gradient-to-r from-primary to-secondary p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">{job.title}</h2>
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
        </div>
      </div>
    </div>
  )
}

export default JobCard
