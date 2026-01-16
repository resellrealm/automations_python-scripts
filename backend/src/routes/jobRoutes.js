import express from 'express'
import {
  getJobs,
  getJobById,
  getSavedJobs,
  saveJob,
  unsaveJob
} from '../controllers/jobController.js'

const router = express.Router()

router.get('/jobs', getJobs)
router.get('/jobs/:id', getJobById)
router.get('/saved-jobs', getSavedJobs)
router.post('/saved-jobs', saveJob)
router.delete('/saved-jobs/:id', unsaveJob)

export default router
