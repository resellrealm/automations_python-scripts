import express from 'express'
import {
  getProfile,
  createProfile,
  updateProfile,
  uploadResume,
  calculateMatches,
  getMatches,
  upload
} from '../controllers/profileController.js'

const router = express.Router()

router.get('/profile', getProfile)
router.post('/profile', createProfile)
router.put('/profile', updateProfile)
router.post('/profile/upload-resume', upload.single('resume'), uploadResume)
router.post('/profile/calculate-matches', calculateMatches)
router.get('/profile/matches', getMatches)

export default router
