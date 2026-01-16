function Header({ currentView, setCurrentView }) {
  return (
    <header className="bg-white shadow-md">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary">Job Swipe</h1>

          <nav className="flex gap-4">
            <button
              onClick={() => setCurrentView('swipe')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                currentView === 'swipe'
                  ? 'bg-primary text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Swipe
            </button>
            <button
              onClick={() => setCurrentView('saved')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                currentView === 'saved'
                  ? 'bg-primary text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Saved Jobs
            </button>
            <button
              onClick={() => setCurrentView('profile')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                currentView === 'profile'
                  ? 'bg-primary text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Profile
            </button>
          </nav>
        </div>
      </div>
    </header>
  )
}

export default Header
