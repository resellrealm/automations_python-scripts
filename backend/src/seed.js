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
    requirements: ['5+ years of experience', 'Proficiency in JavaScript/TypeScript', 'Experience with React and Node.js', 'Strong problem-solving skills']
  },
  {
    title: 'Frontend Developer',
    company: 'WebSolutions Inc',
    location: 'Remote',
    jobType: 'full-time',
    salary: 95000,
    industry: 'technology',
    description: 'Join our team as a frontend developer and help build beautiful, responsive web applications. You will work closely with designers and backend developers.',
    requirements: ['3+ years of frontend experience', 'Expert in React or Vue.js', 'Strong CSS and HTML skills', 'Experience with responsive design']
  },
  {
    title: 'Product Manager',
    company: 'InnovateCo',
    location: 'New York, NY',
    jobType: 'full-time',
    salary: 130000,
    industry: 'technology',
    description: 'We need a product manager to drive product strategy and roadmap. You will work with cross-functional teams to deliver exceptional products.',
    requirements: ['5+ years in product management', 'Strong analytical skills', 'Experience with Agile methodology', 'Excellent communication skills']
  },
  {
    title: 'Data Scientist',
    company: 'DataFlow Analytics',
    location: 'Boston, MA',
    jobType: 'full-time',
    salary: 125000,
    industry: 'technology',
    description: 'Looking for a data scientist to analyze complex datasets and build predictive models. You will work on exciting machine learning projects.',
    requirements: ['PhD or Masters in related field', 'Strong Python and R skills', 'Experience with ML frameworks', 'Statistical analysis expertise']
  },
  {
    title: 'UX Designer',
    company: 'DesignHub',
    location: 'Los Angeles, CA',
    jobType: 'full-time',
    salary: 105000,
    industry: 'design',
    description: 'Create intuitive and engaging user experiences for our products. You will conduct user research and design wireframes and prototypes.',
    requirements: ['4+ years of UX design experience', 'Proficiency in Figma or Sketch', 'Strong portfolio', 'User research experience']
  },
  {
    title: 'DevOps Engineer',
    company: 'CloudTech',
    location: 'Seattle, WA',
    jobType: 'full-time',
    salary: 140000,
    industry: 'technology',
    description: 'Join our DevOps team to build and maintain cloud infrastructure. You will automate deployments and ensure system reliability.',
    requirements: ['Experience with AWS or Azure', 'Knowledge of Docker and Kubernetes', 'CI/CD pipeline expertise', 'Scripting skills (Python, Bash)']
  },
  {
    title: 'Marketing Manager',
    company: 'BrandBoost',
    location: 'Chicago, IL',
    jobType: 'full-time',
    salary: 90000,
    industry: 'marketing',
    description: 'Lead our marketing efforts and develop strategies to grow our brand. You will manage campaigns and analyze marketing metrics.',
    requirements: ['5+ years in marketing', 'Digital marketing expertise', 'Strong analytical skills', 'Team management experience']
  },
  {
    title: 'Full Stack Developer',
    company: 'StartupXYZ',
    location: 'Austin, TX',
    jobType: 'full-time',
    salary: 110000,
    industry: 'technology',
    description: 'Be part of our fast-growing startup as a full stack developer. You will work on both frontend and backend development.',
    requirements: ['3+ years full stack experience', 'Knowledge of React and Node.js', 'Database experience (SQL/NoSQL)', 'Startup mindset']
  },
  {
    title: 'Sales Representative',
    company: 'SalesPro Inc',
    location: 'Miami, FL',
    jobType: 'full-time',
    salary: 75000,
    industry: 'sales',
    description: 'Drive revenue growth by building relationships with clients and closing deals. You will be responsible for meeting sales targets.',
    requirements: ['2+ years in sales', 'Excellent communication skills', 'Track record of meeting quotas', 'CRM experience']
  },
  {
    title: 'Mobile App Developer',
    company: 'AppWorks',
    location: 'Remote',
    jobType: 'full-time',
    salary: 115000,
    industry: 'technology',
    description: 'Develop native mobile applications for iOS and Android. You will work on creating smooth and performant mobile experiences.',
    requirements: ['Experience with React Native or Flutter', 'Understanding of mobile UI/UX', 'API integration skills', 'App store deployment experience']
  },
  {
    title: 'Content Writer',
    company: 'ContentCraft',
    location: 'Remote',
    jobType: 'part-time',
    salary: 50000,
    industry: 'marketing',
    description: 'Create engaging content for our blog, social media, and marketing materials. You will research topics and write compelling articles.',
    requirements: ['Excellent writing skills', 'SEO knowledge', 'Research abilities', 'Portfolio of published work']
  },
  {
    title: 'Financial Analyst',
    company: 'FinanceFirst',
    location: 'New York, NY',
    jobType: 'full-time',
    salary: 95000,
    industry: 'finance',
    description: 'Analyze financial data and create reports to support business decisions. You will work with senior management on strategic planning.',
    requirements: ['Bachelor\'s in Finance or Accounting', 'Strong Excel skills', 'Financial modeling experience', 'CFA or CPA preferred']
  },
  {
    title: 'Quality Assurance Engineer',
    company: 'TestMasters',
    location: 'San Jose, CA',
    jobType: 'full-time',
    salary: 100000,
    industry: 'technology',
    description: 'Ensure software quality through comprehensive testing. You will design test cases and automate testing processes.',
    requirements: ['3+ years in QA', 'Test automation experience', 'Knowledge of testing frameworks', 'Attention to detail']
  },
  {
    title: 'HR Manager',
    company: 'PeopleFirst Corp',
    location: 'Denver, CO',
    jobType: 'full-time',
    salary: 85000,
    industry: 'education',
    description: 'Manage HR operations including recruitment, employee relations, and performance management. You will help build a strong company culture.',
    requirements: ['5+ years in HR', 'Knowledge of employment law', 'Excellent interpersonal skills', 'SHRM certification preferred']
  },
  {
    title: 'Backend Engineer',
    company: 'ServerSide Tech',
    location: 'Portland, OR',
    jobType: 'full-time',
    salary: 120000,
    industry: 'technology',
    description: 'Build robust and scalable backend systems. You will design APIs and work with databases to power our applications.',
    requirements: ['Strong knowledge of Node.js or Python', 'Database design experience', 'RESTful API development', 'Microservices architecture']
  },
  {
    title: 'Graphic Designer',
    company: 'Creative Studio',
    location: 'Remote',
    jobType: 'contract',
    salary: 70000,
    industry: 'design',
    description: 'Create visual content for various digital and print media. You will work on branding, marketing materials, and web graphics.',
    requirements: ['Proficiency in Adobe Creative Suite', 'Strong portfolio', 'Understanding of design principles', '3+ years of experience']
  },
  {
    title: 'Customer Success Manager',
    company: 'SupportHub',
    location: 'Remote',
    jobType: 'full-time',
    salary: 80000,
    industry: 'sales',
    description: 'Help customers achieve success with our products. You will onboard new clients and provide ongoing support.',
    requirements: ['Experience in customer success', 'Strong communication skills', 'Problem-solving abilities', 'SaaS experience preferred']
  },
  {
    title: 'Machine Learning Engineer',
    company: 'AI Innovations',
    location: 'San Francisco, CA',
    jobType: 'full-time',
    salary: 160000,
    industry: 'technology',
    description: 'Develop and deploy machine learning models at scale. You will work on cutting-edge AI projects and research.',
    requirements: ['Advanced degree in CS or related field', 'Strong ML fundamentals', 'TensorFlow or PyTorch experience', 'Research publications a plus']
  },
  {
    title: 'Business Analyst',
    company: 'ConsultPro',
    location: 'Washington, DC',
    jobType: 'full-time',
    salary: 90000,
    industry: 'finance',
    description: 'Bridge the gap between business needs and technical solutions. You will gather requirements and analyze business processes.',
    requirements: ['3+ years as business analyst', 'Requirements gathering experience', 'SQL knowledge', 'Strong analytical skills']
  },
  {
    title: 'Cybersecurity Specialist',
    company: 'SecureNet',
    location: 'Remote',
    jobType: 'full-time',
    salary: 135000,
    industry: 'technology',
    description: 'Protect our systems and data from security threats. You will conduct security audits and respond to incidents.',
    requirements: ['Security certifications (CISSP, CEH)', 'Network security knowledge', 'Incident response experience', 'Ethical hacking skills']
  },
  {
    title: 'Project Manager',
    company: 'BuildIt Inc',
    location: 'Houston, TX',
    jobType: 'full-time',
    salary: 105000,
    industry: 'engineering',
    description: 'Lead project teams to deliver projects on time and within budget. You will manage resources and stakeholder communication.',
    requirements: ['PMP certification', '5+ years in project management', 'Agile experience', 'Strong leadership skills']
  },
  {
    title: 'Video Editor',
    company: 'MediaWorks',
    location: 'Los Angeles, CA',
    jobType: 'contract',
    salary: 65000,
    industry: 'design',
    description: 'Edit video content for various platforms including social media, websites, and advertising campaigns.',
    requirements: ['Proficiency in Premiere Pro or Final Cut', 'Motion graphics skills', 'Portfolio of work', 'Attention to detail']
  },
  {
    title: 'Software Engineering Intern',
    company: 'FutureTech',
    location: 'Palo Alto, CA',
    jobType: 'internship',
    salary: 35000,
    industry: 'technology',
    description: 'Gain hands-on experience in software development. You will work with experienced engineers on real projects.',
    requirements: ['Currently pursuing CS degree', 'Basic programming knowledge', 'Eagerness to learn', 'Problem-solving skills']
  },
  {
    title: 'Nurse Practitioner',
    company: 'HealthCare Plus',
    location: 'Boston, MA',
    jobType: 'full-time',
    salary: 110000,
    industry: 'healthcare',
    description: 'Provide primary and specialty healthcare services to patients. You will diagnose conditions and prescribe treatments.',
    requirements: ['NP certification', 'Active state license', 'Clinical experience', 'Excellent patient care skills']
  },
  {
    title: 'Social Media Manager',
    company: 'SocialBuzz',
    location: 'Remote',
    jobType: 'full-time',
    salary: 70000,
    industry: 'marketing',
    description: 'Manage our social media presence across all platforms. You will create content and engage with our community.',
    requirements: ['3+ years in social media management', 'Content creation skills', 'Analytics expertise', 'Understanding of social platforms']
  }
]

console.log('Seeding database with sample jobs...')

sampleJobs.forEach(job => {
  try {
    Job.create(job)
    console.log(`Added: ${job.title} at ${job.company}`)
  } catch (error) {
    console.error(`Error adding ${job.title}:`, error.message)
  }
})

console.log('Database seeding completed!')
