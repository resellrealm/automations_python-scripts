import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import jobRoutes from './routes/jobRoutes.js'
import profileRoutes from './routes/profileRoutes.js'
import './config/database.js'

dotenv.config()

const app = express()
const PORT = process.env.PORT || 5000

app.use(cors())
app.use(express.json())

app.use('/api', jobRoutes)
app.use('/api', profileRoutes)

app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', message: 'Job Swipe API is running' })
})

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`)
  console.log(`API available at http://localhost:${PORT}/api`)
})
