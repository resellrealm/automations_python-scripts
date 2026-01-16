import { useState, useEffect } from 'react'

function Profile({ onBack }) {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [calculating, setCalculating] = useState(false)
  const [message, setMessage] = useState(null)
  const [editMode, setEditMode] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    location: ''
  })

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/profile')
      if (response.ok) {
        const data = await response.json()
        setProfile(data)
        setFormData({
          name: data.name || '',
          email: data.email || '',
          phone: data.phone || '',
          location: data.location || ''
        })
      }
    } catch (error) {
      console.error('Error fetching profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (file.type !== 'application/pdf' && file.type !== 'text/plain') {
      setMessage({ type: 'error', text: 'Please upload a PDF or TXT file' })
      return
    }

    const formData = new FormData()
    formData.append('resume', file)

    try {
      setUploading(true)
      setMessage({ type: 'info', text: 'Uploading and parsing your resume with AI...' })

      const response = await fetch('/api/profile/upload-resume', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error('Failed to upload resume')
      }

      const data = await response.json()
      setMessage({ type: 'success', text: 'Resume uploaded and parsed successfully!' })
      await fetchProfile()
    } catch (error) {
      console.error('Error uploading resume:', error)
      setMessage({ type: 'error', text: 'Failed to upload resume. Please try again.' })
    } finally {
      setUploading(false)
    }
  }

  const handleCalculateMatches = async () => {
    if (!profile) {
      setMessage({ type: 'error', text: 'Please upload a resume first' })
      return
    }

    try {
      setCalculating(true)
      setMessage({ type: 'info', text: 'Calculating job matches with AI... This may take a minute.' })

      const response = await fetch('/api/profile/calculate-matches', {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error('Failed to calculate matches')
      }

      const data = await response.json()
      setMessage({ type: 'success', text: `Successfully calculated matches for ${data.matchCount} jobs!` })

      setTimeout(() => {
        onBack()
      }, 2000)
    } catch (error) {
      console.error('Error calculating matches:', error)
      setMessage({ type: 'error', text: 'Failed to calculate matches. Please check your API key.' })
    } finally {
      setCalculating(false)
    }
  }

  const handleUpdateProfile = async (e) => {
    e.preventDefault()

    try {
      setLoading(true)
      const response = await fetch('/api/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      if (!response.ok) {
        throw new Error('Failed to update profile')
      }

      setMessage({ type: 'success', text: 'Profile updated successfully!' })
      setEditMode(false)
      await fetchProfile()
    } catch (error) {
      console.error('Error updating profile:', error)
      setMessage({ type: 'error', text: 'Failed to update profile' })
    } finally {
      setLoading(false)
    }
  }

  if (loading && !profile) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="text-white text-xl">Loading profile...</div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-white">Your Profile</h2>
        <button
          onClick={onBack}
          className="bg-white text-primary px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          Back to Jobs
        </button>
      </div>

      {message && (
        <div className={`mb-6 p-4 rounded-lg ${
          message.type === 'error' ? 'bg-red-100 text-red-700' :
          message.type === 'success' ? 'bg-green-100 text-green-700' :
          'bg-blue-100 text-blue-700'
        }`}>
          {message.text}
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
        <h3 className="text-2xl font-bold text-gray-800 mb-6">Resume Upload</h3>

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <div className="text-6xl mb-4">📄</div>
          <h4 className="text-lg font-semibold text-gray-700 mb-2">
            {profile?.resumeFileName || 'Upload Your Resume'}
          </h4>
          <p className="text-gray-600 mb-4">
            Upload a PDF or TXT file. AI will automatically extract your information.
          </p>
          <label className="inline-block">
            <input
              type="file"
              accept=".pdf,.txt"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
            <span className={`bg-primary text-white px-6 py-3 rounded-lg font-medium cursor-pointer hover:bg-indigo-700 transition-colors inline-block ${
              uploading ? 'opacity-50 cursor-not-allowed' : ''
            }`}>
              {uploading ? 'Processing...' : profile ? 'Upload New Resume' : 'Upload Resume'}
            </span>
          </label>
        </div>
      </div>

      {profile && (
        <>
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-gray-800">Personal Information</h3>
              <button
                onClick={() => setEditMode(!editMode)}
                className="text-primary hover:text-indigo-700 font-medium"
              >
                {editMode ? 'Cancel' : 'Edit'}
              </button>
            </div>

            {editMode ? (
              <form onSubmit={handleUpdateProfile} className="space-y-4">
                <div>
                  <label className="block text-gray-700 font-medium mb-2">Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-gray-700 font-medium mb-2">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-gray-700 font-medium mb-2">Phone</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-gray-700 font-medium mb-2">Location</label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary outline-none"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Save Changes
                </button>
              </form>
            ) : (
              <div className="space-y-3">
                <div>
                  <span className="font-semibold text-gray-700">Name:</span>{' '}
                  <span className="text-gray-600">{profile.name || 'Not set'}</span>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">Email:</span>{' '}
                  <span className="text-gray-600">{profile.email || 'Not set'}</span>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">Phone:</span>{' '}
                  <span className="text-gray-600">{profile.phone || 'Not set'}</span>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">Location:</span>{' '}
                  <span className="text-gray-600">{profile.location || 'Not set'}</span>
                </div>
              </div>
            )}
          </div>

          {profile.skills && profile.skills.length > 0 && (
            <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
              <h3 className="text-2xl font-bold text-gray-800 mb-4">Skills</h3>
              <div className="flex flex-wrap gap-2">
                {profile.skills.map((skill, index) => (
                  <span
                    key={index}
                    className="bg-primary text-white px-4 py-2 rounded-full text-sm"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {profile.experience && profile.experience.length > 0 && (
            <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
              <h3 className="text-2xl font-bold text-gray-800 mb-4">Experience</h3>
              <div className="space-y-4">
                {profile.experience.map((exp, index) => (
                  <div key={index} className="border-l-4 border-primary pl-4">
                    <h4 className="font-semibold text-gray-800">{exp.title}</h4>
                    <p className="text-gray-600">{exp.company}</p>
                    <p className="text-sm text-gray-500">{exp.duration}</p>
                    {exp.description && (
                      <p className="text-sm text-gray-600 mt-2">{exp.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {profile.education && profile.education.length > 0 && (
            <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
              <h3 className="text-2xl font-bold text-gray-800 mb-4">Education</h3>
              <div className="space-y-3">
                {profile.education.map((edu, index) => (
                  <div key={index}>
                    <h4 className="font-semibold text-gray-800">{edu.degree}</h4>
                    <p className="text-gray-600">{edu.institution}</p>
                    <p className="text-sm text-gray-500">{edu.year}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-gradient-to-r from-primary to-secondary rounded-2xl shadow-xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4">AI Job Matching</h3>
            <p className="mb-6">
              Use AI to analyze your profile and calculate match scores for all available jobs.
              This will help you find the best opportunities based on your skills and experience.
            </p>
            <button
              onClick={handleCalculateMatches}
              disabled={calculating}
              className={`bg-white text-primary px-8 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors ${
                calculating ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {calculating ? 'Calculating Matches...' : 'Calculate Job Matches'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}

export default Profile
