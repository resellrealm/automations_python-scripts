import { useState, useEffect } from 'react'
import SwipeCards from './components/SwipeCards'
import SavedJobs from './components/SavedJobs'
import Filters from './components/Filters'
import Header from './components/Header'

function App() {
  const [currentView, setCurrentView] = useState('swipe')
  const [jobs, setJobs] = useState([])
  const [savedJobs, setSavedJobs] = useState([])
  const [filters, setFilters] = useState({
    location: '',
    jobType: '',
    minSalary: '',
    industry: ''
  })

  useEffect(() => {
    fetchJobs()
    fetchSavedJobs()
  }, [filters])

  const fetchJobs = async () => {
    try {
      const params = new URLSearchParams()
      if (filters.location) params.append('location', filters.location)
      if (filters.jobType) params.append('jobType', filters.jobType)
      if (filters.minSalary) params.append('minSalary', filters.minSalary)
      if (filters.industry) params.append('industry', filters.industry)

      const response = await fetch(`/api/jobs?${params}`)
      const data = await response.json()
      setJobs(data)
    } catch (error) {
      console.error('Error fetching jobs:', error)
    }
  }

  const fetchSavedJobs = async () => {
    try {
      const response = await fetch('/api/saved-jobs')
      const data = await response.json()
      setSavedJobs(data)
    } catch (error) {
      console.error('Error fetching saved jobs:', error)
    }
  }

  const handleSwipe = async (jobId, direction) => {
    if (direction === 'right') {
      try {
        await fetch('/api/saved-jobs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ jobId })
        })
        fetchSavedJobs()
      } catch (error) {
        console.error('Error saving job:', error)
      }
    }

    setJobs(prev => prev.filter(job => job.id !== jobId))
  }

  const handleUnsave = async (jobId) => {
    try {
      await fetch(`/api/saved-jobs/${jobId}`, { method: 'DELETE' })
      fetchSavedJobs()
    } catch (error) {
      console.error('Error unsaving job:', error)
    }
  }

  const handleApplyFilters = (newFilters) => {
    setFilters(newFilters)
    setCurrentView('swipe')
  }

  return (
    <div className="min-h-screen">
      <Header currentView={currentView} setCurrentView={setCurrentView} />

      <div className="container mx-auto px-4 py-8">
        {currentView === 'swipe' && (
          <SwipeCards jobs={jobs} onSwipe={handleSwipe} onFilterClick={() => setCurrentView('filters')} />
        )}

        {currentView === 'saved' && (
          <SavedJobs jobs={savedJobs} onUnsave={handleUnsave} />
        )}

        {currentView === 'filters' && (
          <Filters currentFilters={filters} onApplyFilters={handleApplyFilters} />
        )}
      </div>
    </div>
  )
}

export default App
