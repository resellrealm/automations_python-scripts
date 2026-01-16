import { Job } from './models/Job.js'

const sampleJobs = [
  {
    title: 'Senior Software Engineer',
    company: 'TechCorp',
    location: 'San Francisco, CA',
    jobType: 'full-time',
    salary: 150000,
    industry: 'technology',
    description: 'We are looking for a senior software engineer to join our dynamic team. You will be responsible for designing, developing, and maintaining scalable applications.',
    requirements: ['5+ years of experience', 'Proficiency in JavaScript/TypeScript', 'Experience with React and Node.js', 'Strong problem-solving skills'],
    applicationUrl: 'https://jobs.lever.co/techcorp/senior-software-engineer',
    companyWebsite: 'https://techcorp.com/careers',
    contactEmail: 'careers@techcorp.com',
    applicationNotes: 'Apply via Lever. Include GitHub profile link.'
  },
  {
    title: 'Frontend Developer',
    company: 'WebSolutions Inc',
    location: 'Remote',
    jobType: 'full-time',
    salary: 95000,
    industry: 'technology',
    description: 'Join our team as a frontend developer and help build beautiful, responsive web applications. You will work closely with designers and backend developers.',
    requirements: ['3+ years of frontend experience', 'Expert in React or Vue.js', 'Strong CSS and HTML skills', 'Experience with responsive design'],
    applicationUrl: 'https://websolutions.com/careers/frontend-developer',
    companyWebsite: 'https://websolutions.com',
    contactEmail: 'hiring@websolutions.com',
    applicationNotes: 'Submit portfolio with application. Remote-first company.'
  },
  {
    title: 'Product Manager',
    company: 'InnovateCo',
    location: 'New York, NY',
    jobType: 'full-time',
    salary: 130000,
    industry: 'technology',
    description: 'We need a product manager to drive product strategy and roadmap. You will work with cross-functional teams to deliver exceptional products.',
    requirements: ['5+ years in product management', 'Strong analytical skills', 'Experience with Agile methodology', 'Excellent communication skills'],
    applicationUrl: 'https://www.linkedin.com/jobs/view/product-manager-innovateco',
    companyWebsite: 'https://innovateco.io',
    contactEmail: 'jobs@innovateco.io',
    applicationNotes: 'LinkedIn application. Prepare case study presentation.'
  },
  {
    title: 'Data Scientist',
    company: 'DataFlow Analytics',
    location: 'Boston, MA',
    jobType: 'full-time',
    salary: 125000,
    industry: 'technology',
    description: 'Looking for a data scientist to analyze complex datasets and build predictive models. You will work on exciting machine learning projects.',
    requirements: ['PhD or Masters in related field', 'Strong Python and R skills', 'Experience with ML frameworks', 'Statistical analysis expertise'],
    applicationUrl: 'https://dataflow.com/jobs/data-scientist',
    companyWebsite: 'https://dataflowanalytics.com',
    contactEmail: 'talent@dataflow.com',
    applicationNotes: 'Include link to Kaggle profile or ML project portfolio.'
  },
  {
    title: 'UX Designer',
    company: 'DesignHub',
    location: 'Los Angeles, CA',
    jobType: 'full-time',
    salary: 105000,
    industry: 'design',
    description: 'Create intuitive and engaging user experiences for our products. You will conduct user research and design wireframes and prototypes.',
    requirements: ['4+ years of UX design experience', 'Proficiency in Figma or Sketch', 'Strong portfolio', 'User research experience'],
    applicationUrl: 'https://designhub.io/careers/ux-designer',
    companyWebsite: 'https://designhub.io',
    contactEmail: 'design-jobs@designhub.io',
    applicationNotes: 'Portfolio review required. Figma link preferred.'
  },
  {
    title: 'DevOps Engineer',
    company: 'CloudTech',
    location: 'Seattle, WA',
    jobType: 'full-time',
    salary: 140000,
    industry: 'technology',
    description: 'Join our DevOps team to build and maintain cloud infrastructure. You will automate deployments and ensure system reliability.',
    requirements: ['Experience with AWS or Azure', 'Knowledge of Docker and Kubernetes', 'CI/CD pipeline expertise', 'Scripting skills (Python, Bash)'],
    applicationUrl: 'https://greenhouse.io/cloudtech/devops-engineer',
    companyWebsite: 'https://cloudtech.com',
    contactEmail: 'devops-hiring@cloudtech.com',
    applicationNotes: 'Technical screening includes live coding. AWS certifications a plus.'
  },
  {
    title: 'Marketing Manager',
    company: 'BrandBoost',
    location: 'Chicago, IL',
    jobType: 'full-time',
    salary: 90000,
    industry: 'marketing',
    description: 'Lead our marketing efforts and develop strategies to grow our brand. You will manage campaigns and analyze marketing metrics.',
    requirements: ['5+ years in marketing', 'Digital marketing expertise', 'Strong analytical skills', 'Team management experience'],
    applicationUrl: 'https://www.indeed.com/job/marketing-manager-brandboost',
    companyWebsite: 'https://brandboost.com',
    contactEmail: 'hr@brandboost.com',
    applicationNotes: 'Apply via Indeed. Include campaign examples and ROI metrics.'
  },
  {
    title: 'Full Stack Developer',
    company: 'StartupXYZ',
    location: 'Austin, TX',
    jobType: 'full-time',
    salary: 110000,
    industry: 'technology',
    description: 'Be part of our fast-growing startup as a full stack developer. You will work on both frontend and backend development.',
    requirements: ['3+ years full stack experience', 'Knowledge of React and Node.js', 'Database experience (SQL/NoSQL)', 'Startup mindset'],
    applicationUrl: 'https://angel.co/company/startupxyz/jobs',
    companyWebsite: 'https://startupxyz.com',
    contactEmail: 'founders@startupxyz.com',
    applicationNotes: 'AngelList application. Equity compensation available.'
  },
  {
    title: 'Sales Representative',
    company: 'SalesPro Inc',
    location: 'Miami, FL',
    jobType: 'full-time',
    salary: 75000,
    industry: 'sales',
    description: 'Drive revenue growth by building relationships with clients and closing deals. You will be responsible for meeting sales targets.',
    requirements: ['2+ years in sales', 'Excellent communication skills', 'Track record of meeting quotas', 'CRM experience'],
    applicationUrl: 'https://salespro.com/careers/sales-rep',
    companyWebsite: 'https://salespro.com',
    contactEmail: 'sales-jobs@salespro.com',
    applicationNotes: 'Commission structure included. Base + commission.'
  },
  {
    title: 'Mobile App Developer',
    company: 'AppWorks',
    location: 'Remote',
    jobType: 'full-time',
    salary: 115000,
    industry: 'technology',
    description: 'Develop native mobile applications for iOS and Android. You will work on creating smooth and performant mobile experiences.',
    requirements: ['Experience with React Native or Flutter', 'Understanding of mobile UI/UX', 'API integration skills', 'App store deployment experience'],
    applicationUrl: 'https://appworks.io/jobs/mobile-developer',
    companyWebsite: 'https://appworks.io',
    contactEmail: 'mobile-team@appworks.io',
    applicationNotes: 'Include links to published apps on App Store/Play Store.'
  },
  {
    title: 'Content Writer',
    company: 'ContentCraft',
    location: 'Remote',
    jobType: 'part-time',
    salary: 50000,
    industry: 'marketing',
    description: 'Create engaging content for our blog, social media, and marketing materials. You will research topics and write compelling articles.',
    requirements: ['Excellent writing skills', 'SEO knowledge', 'Research abilities', 'Portfolio of published work'],
    applicationUrl: 'https://contentcraft.com/apply',
    companyWebsite: 'https://contentcraft.com',
    contactEmail: 'writers@contentcraft.com',
    applicationNotes: 'Submit 3 writing samples. SEO writing experience required.'
  },
  {
    title: 'Financial Analyst',
    company: 'FinanceFirst',
    location: 'New York, NY',
    jobType: 'full-time',
    salary: 95000,
    industry: 'finance',
    description: 'Analyze financial data and create reports to support business decisions. You will work with senior management on strategic planning.',
    requirements: ["Bachelor's in Finance or Accounting", 'Strong Excel skills', 'Financial modeling experience', 'CFA or CPA preferred'],
    applicationUrl: 'https://www.linkedin.com/jobs/view/financial-analyst-financefirst',
    companyWebsite: 'https://financefirst.com',
    contactEmail: 'recruiting@financefirst.com',
    applicationNotes: 'Bloomberg terminal experience preferred. CFA candidates encouraged.'
  },
  {
    title: 'Quality Assurance Engineer',
    company: 'TestMasters',
    location: 'San Jose, CA',
    jobType: 'full-time',
    salary: 100000,
    industry: 'technology',
    description: 'Ensure software quality through comprehensive testing. You will design test cases and automate testing processes.',
    requirements: ['3+ years in QA', 'Test automation experience', 'Knowledge of testing frameworks', 'Attention to detail'],
    applicationUrl: 'https://testmasters.com/careers/qa-engineer',
    companyWebsite: 'https://testmasters.com',
    contactEmail: 'qa-jobs@testmasters.com',
    applicationNotes: 'Selenium/Cypress experience required. ISTQB certification a plus.'
  },
  {
    title: 'HR Manager',
    company: 'PeopleFirst Corp',
    location: 'Denver, CO',
    jobType: 'full-time',
    salary: 85000,
    industry: 'education',
    description: 'Manage HR operations including recruitment, employee relations, and performance management. You will help build a strong company culture.',
    requirements: ['5+ years in HR', 'Knowledge of employment law', 'Excellent interpersonal skills', 'SHRM certification preferred'],
    applicationUrl: 'https://peoplefirst.com/jobs/hr-manager',
    companyWebsite: 'https://peoplefirstcorp.com',
    contactEmail: 'hr@peoplefirstcorp.com',
    applicationNotes: 'SHRM-CP/SCP certification preferred. Benefits-focused role.'
  },
  {
    title: 'Backend Engineer',
    company: 'ServerSide Tech',
    location: 'Portland, OR',
    jobType: 'full-time',
    salary: 120000,
    industry: 'technology',
    description: 'Build robust and scalable backend systems. You will design APIs and work with databases to power our applications.',
    requirements: ['Strong knowledge of Node.js or Python', 'Database design experience', 'RESTful API development', 'Microservices architecture'],
    applicationUrl: 'https://jobs.lever.co/serverside/backend-engineer',
    companyWebsite: 'https://serversidetech.com',
    contactEmail: 'backend-jobs@serversidetech.com',
    applicationNotes: 'System design interview included. GraphQL experience a plus.'
  },
  {
    title: 'Graphic Designer',
    company: 'Creative Studio',
    location: 'Remote',
    jobType: 'contract',
    salary: 70000,
    industry: 'design',
    description: 'Create visual content for various digital and print media. You will work on branding, marketing materials, and web graphics.',
    requirements: ['Proficiency in Adobe Creative Suite', 'Strong portfolio', 'Understanding of design principles', '3+ years of experience'],
    applicationUrl: 'https://creativestudio.com/freelance/graphic-designer',
    companyWebsite: 'https://creativestudio.com',
    contactEmail: 'design@creativestudio.com',
    applicationNotes: 'Contract position. Portfolio required - PDF or Behance link.'
  },
  {
    title: 'Customer Success Manager',
    company: 'SupportHub',
    location: 'Remote',
    jobType: 'full-time',
    salary: 80000,
    industry: 'sales',
    description: 'Help customers achieve success with our products. You will onboard new clients and provide ongoing support.',
    requirements: ['Experience in customer success', 'Strong communication skills', 'Problem-solving abilities', 'SaaS experience preferred'],
    applicationUrl: 'https://supporthub.com/careers/customer-success',
    companyWebsite: 'https://supporthub.com',
    contactEmail: 'csm-hiring@supporthub.com',
    applicationNotes: 'Remote role. Experience with Salesforce and Zendesk preferred.'
  },
  {
    title: 'Machine Learning Engineer',
    company: 'AI Innovations',
    location: 'San Francisco, CA',
    jobType: 'full-time',
    salary: 160000,
    industry: 'technology',
    description: 'Develop and deploy machine learning models at scale. You will work on cutting-edge AI projects and research.',
    requirements: ['Advanced degree in CS or related field', 'Strong ML fundamentals', 'TensorFlow or PyTorch experience', 'Research publications a plus'],
    applicationUrl: 'https://aiinnovations.com/jobs/ml-engineer',
    companyWebsite: 'https://aiinnovations.com',
    contactEmail: 'ml-team@aiinnovations.com',
    applicationNotes: 'PhD preferred. Include research papers or ML project demos.'
  },
  {
    title: 'Business Analyst',
    company: 'ConsultPro',
    location: 'Washington, DC',
    jobType: 'full-time',
    salary: 90000,
    industry: 'finance',
    description: 'Bridge the gap between business needs and technical solutions. You will gather requirements and analyze business processes.',
    requirements: ['3+ years as business analyst', 'Requirements gathering experience', 'SQL knowledge', 'Strong analytical skills'],
    applicationUrl: 'https://www.indeed.com/job/business-analyst-consultpro',
    companyWebsite: 'https://consultpro.com',
    contactEmail: 'ba-jobs@consultpro.com',
    applicationNotes: 'Government contract work. Clearance required or obtainable.'
  },
  {
    title: 'Cybersecurity Specialist',
    company: 'SecureNet',
    location: 'Remote',
    jobType: 'full-time',
    salary: 135000,
    industry: 'technology',
    description: 'Protect our systems and data from security threats. You will conduct security audits and respond to incidents.',
    requirements: ['Security certifications (CISSP, CEH)', 'Network security knowledge', 'Incident response experience', 'Ethical hacking skills'],
    applicationUrl: 'https://securenet.com/careers/cybersecurity',
    companyWebsite: 'https://securenet.com',
    contactEmail: 'security-jobs@securenet.com',
    applicationNotes: 'CISSP required. Pen testing skills highly valued.'
  },
  {
    title: 'Project Manager',
    company: 'BuildIt Inc',
    location: 'Houston, TX',
    jobType: 'full-time',
    salary: 105000,
    industry: 'engineering',
    description: 'Lead project teams to deliver projects on time and within budget. You will manage resources and stakeholder communication.',
    requirements: ['PMP certification', '5+ years in project management', 'Agile experience', 'Strong leadership skills'],
    applicationUrl: 'https://buildit.com/jobs/project-manager',
    companyWebsite: 'https://builditinc.com',
    contactEmail: 'pm-hiring@builditinc.com',
    applicationNotes: 'PMP certification required. Construction industry experience a plus.'
  },
  {
    title: 'Video Editor',
    company: 'MediaWorks',
    location: 'Los Angeles, CA',
    jobType: 'contract',
    salary: 65000,
    industry: 'design',
    description: 'Edit video content for various platforms including social media, websites, and advertising campaigns.',
    requirements: ['Proficiency in Premiere Pro or Final Cut', 'Motion graphics skills', 'Portfolio of work', 'Attention to detail'],
    applicationUrl: 'https://mediaworks.com/freelance/video-editor',
    companyWebsite: 'https://mediaworks.com',
    contactEmail: 'video@mediaworks.com',
    applicationNotes: 'Contract role. Submit video reel with application.'
  },
  {
    title: 'Software Engineering Intern',
    company: 'FutureTech',
    location: 'Palo Alto, CA',
    jobType: 'internship',
    salary: 35000,
    industry: 'technology',
    description: 'Gain hands-on experience in software development. You will work with experienced engineers on real projects.',
    requirements: ['Currently pursuing CS degree', 'Basic programming knowledge', 'Eagerness to learn', 'Problem-solving skills'],
    applicationUrl: 'https://futuretech.com/internships/software-engineering',
    companyWebsite: 'https://futuretech.com',
    contactEmail: 'internships@futuretech.com',
    applicationNotes: 'Summer 2026 internship. Undergrads and recent grads welcome.'
  },
  {
    title: 'Nurse Practitioner',
    company: 'HealthCare Plus',
    location: 'Boston, MA',
    jobType: 'full-time',
    salary: 110000,
    industry: 'healthcare',
    description: 'Provide primary and specialty healthcare services to patients. You will diagnose conditions and prescribe treatments.',
    requirements: ['NP certification', 'Active state license', 'Clinical experience', 'Excellent patient care skills'],
    applicationUrl: 'https://healthcareplus.com/careers/nurse-practitioner',
    companyWebsite: 'https://healthcareplus.com',
    contactEmail: 'nursing-jobs@healthcareplus.com',
    applicationNotes: 'Massachusetts license required. Sign-on bonus available.'
  },
  {
    title: 'Social Media Manager',
    company: 'SocialBuzz',
    location: 'Remote',
    jobType: 'full-time',
    salary: 70000,
    industry: 'marketing',
    description: 'Manage our social media presence across all platforms. You will create content and engage with our community.',
    requirements: ['3+ years in social media management', 'Content creation skills', 'Analytics expertise', 'Understanding of social platforms'],
    applicationUrl: 'https://socialbuzz.com/jobs/social-media-manager',
    companyWebsite: 'https://socialbuzz.com',
    contactEmail: 'social@socialbuzz.com',
    applicationNotes: 'Remote position. Include examples of successful campaigns.'
  }
]

console.log('Seeding database with sample jobs...')

// Clear existing jobs first
try {
  const db = (await import('../config/database.js')).default
  db.prepare('DELETE FROM jobs').run()
  console.log('Cleared existing jobs')
} catch (error) {
  console.log('Note: Could not clear existing jobs (may be first run)')
}

sampleJobs.forEach(job => {
  try {
    Job.create(job)
    console.log(`Added: ${job.title} at ${job.company}`)
  } catch (error) {
    console.error(`Error adding ${job.title}:`, error.message)
  }
})

console.log('Database seeding completed!')
console.log('\nIMPORTANT: These are sample job listings with placeholder URLs.')
console.log('To use this app for real job hunting:')
console.log('1. Replace sample jobs with real job postings')
console.log('2. Add actual application URLs from company career pages')
console.log('3. Update contact emails with real hiring managers')
console.log('4. Or use this as a template to track jobs you find on LinkedIn/Indeed')
