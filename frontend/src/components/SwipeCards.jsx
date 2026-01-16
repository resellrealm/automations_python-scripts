import { useState } from 'react'
import { useSpring, animated } from '@react-spring/web'
import { useDrag } from '@use-gesture/react'
import JobCard from './JobCard'

function SwipeCards({ jobs, onSwipe, onFilterClick }) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [{ x, rotate }, api] = useSpring(() => ({ x: 0, rotate: 0 }))

  const bind = useDrag(({ down, movement: [mx], direction: [xDir], velocity }) => {
    const trigger = velocity > 0.2
    const dir = xDir < 0 ? -1 : 1

    if (!down && trigger) {
      const direction = dir === 1 ? 'right' : 'left'
      api.start({ x: dir * 1000, rotate: dir * 45 })

      setTimeout(() => {
        onSwipe(jobs[currentIndex].id, direction)
        setCurrentIndex(prev => prev + 1)
        api.start({ x: 0, rotate: 0, immediate: true })
      }, 300)
    } else {
      api.start({
        x: down ? mx : 0,
        rotate: down ? mx / 10 : 0,
        immediate: down
      })
    }
  })

  const handleButtonSwipe = (direction) => {
    const dir = direction === 'right' ? 1 : -1
    api.start({ x: dir * 1000, rotate: dir * 45 })

    setTimeout(() => {
      onSwipe(jobs[currentIndex].id, direction)
      setCurrentIndex(prev => prev + 1)
      api.start({ x: 0, rotate: 0, immediate: true })
    }, 300)
  }

  if (jobs.length === 0 || currentIndex >= jobs.length) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <div className="bg-white rounded-2xl p-8 shadow-xl text-center max-w-md">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">No More Jobs!</h2>
          <p className="text-gray-600 mb-6">You've seen all available jobs. Check back later for new opportunities!</p>
          <button
            onClick={onFilterClick}
            className="bg-primary text-white px-6 py-3 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
          >
            Adjust Filters
          </button>
        </div>
      </div>
    )
  }

  const currentJob = jobs[currentIndex]

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-full max-w-md h-[600px] mb-8">
        <animated.div
          {...bind()}
          style={{
            x,
            rotate: rotate.to(r => `${r}deg`),
            touchAction: 'none',
          }}
          className="absolute w-full h-full cursor-grab active:cursor-grabbing"
        >
          <JobCard job={currentJob} />
        </animated.div>

        {currentIndex + 1 < jobs.length && (
          <div className="absolute w-full h-full" style={{ transform: 'scale(0.95)', zIndex: -1 }}>
            <JobCard job={jobs[currentIndex + 1]} />
          </div>
        )}
      </div>

      <div className="flex gap-6">
        <button
          onClick={() => handleButtonSwipe('left')}
          className="bg-white text-danger border-2 border-danger w-16 h-16 rounded-full shadow-lg hover:bg-danger hover:text-white transition-all transform hover:scale-110 flex items-center justify-center font-bold text-2xl"
        >
          ✕
        </button>
        <button
          onClick={onFilterClick}
          className="bg-white text-primary border-2 border-primary w-16 h-16 rounded-full shadow-lg hover:bg-primary hover:text-white transition-all transform hover:scale-110 flex items-center justify-center font-bold text-2xl"
        >
          ⚙
        </button>
        <button
          onClick={() => handleButtonSwipe('right')}
          className="bg-white text-success border-2 border-success w-16 h-16 rounded-full shadow-lg hover:bg-success hover:text-white transition-all transform hover:scale-110 flex items-center justify-center font-bold text-2xl"
        >
          ♥
        </button>
      </div>

      <div className="mt-6 text-white text-sm">
        {currentIndex + 1} / {jobs.length}
      </div>
    </div>
  )
}

export default SwipeCards
