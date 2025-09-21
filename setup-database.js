// setup-database.js - Run this script to initialize the database structure

const fs = require('fs');
const path = require('path');

// Database structure for each user
const USER_DATA_STRUCTURE = {
  profile: {
    userId: '',
    email: '',
    username: '',
    password: '', // hashed
    createdAt: '',
    lastLogin: '',
    preferences: {
      answerLength: 'medium',
      analogyStyle: 'general',
      bloomsLevel: 'analyze',
      studyStreak: 0,
      focusLevel: 'medium',
      theme: 'dark'
    },
    analytics: {
      questionsAsked: 0,
      conceptsLearned: [],
      weakAreas: [],
      studyTime: 0,
      bloomsLevels: {
        remember: 0,
        understand: 0,
        apply: 0,
        analyze: 0,
        evaluate: 0,
        create: 0
      }
    }
  },
  
  pdfs: {
    // filename: {
    //   id: 'unique-id',
    //   originalName: 'document.pdf',
    //   filename: 'stored-filename.pdf',
    //   uploadedAt: 'timestamp',
    //   size: 'file-size',
    //   extractedText: 'full-text-content',
    //   metadata: {
    //     pages: 0,
    //     subject: 'auto-detected-subject',
    //     keywords: ['keyword1', 'keyword2']
    //   },
    //   chunks: [
    //     {
    //       id: 'chunk-1',
    //       text: 'text-chunk',
    //       page: 1,
    //       embedding: [] // for future vector search
    //     }
    //   ]
    // }
  },
  
  flashcards: {
    userMade: [
      // {
      //   id: 'card-id',
      //   question: 'question',
      //   answer: 'answer',
      //   subject: 'subject',
      //   difficulty: 5,
      //   createdAt: 'timestamp',
      //   lastReviewed: 'timestamp',
      //   reviewCount: 0,
      //   correctCount: 0,
      //   tags: ['tag1', 'tag2']
      // }
    ],
    aiGenerated: [
      // Same structure as userMade
      // {
      //   id: 'card-id',
      //   question: 'ai-generated-question',
      //   answer: 'ai-generated-answer',
      //   subject: 'subject',
      //   difficulty: 5,
      //   createdAt: 'timestamp',
      //   sourceDocument: 'pdf-id', // if generated from PDF
      //   lastReviewed: 'timestamp',
      //   reviewCount: 0,
      //   correctCount: 0,
      //   tags: ['ai-generated']
      // }
    ]
  },
  
  bookmarks: [
    // {
    //   id: 'bookmark-id',
    //   type: 'question', // 'question', 'flashcard', 'pdf-section'
    //   content: 'bookmarked-content',
    //   metadata: {
    //     question: 'original-question',
    //     answer: 'answer',
    //     source: 'ai/dataset/pdf',
    //     subject: 'subject'
    //   },
    //   createdAt: 'timestamp',
    //   tags: ['important', 'review-later']
    // }
  ],
  
  studyStreaks: {
    currentStreak: 0,
    longestStreak: 0,
    lastStudyDate: '',
    streakHistory: [
      // {
      //   date: 'YYYY-MM-DD',
      //   questionsAnswered: 0,
      //   studyTimeMinutes: 0,
      //   subjects: ['math', 'science']
      // }
    ]
  },
  
  chatHistory: [
    // {
    //   id: 'chat-id',
    //   timestamp: 'timestamp',
    //   question: 'user-question',
    //   answer: 'bot-response',
    //   metadata: {
    //     mode: 'normal',
    //     subject: 'subject',
    //     source: 'ai/dataset/pdf',
    //     accuracy: 85,
    //     bloomsLevel: 'analyze',
    //     difficulty: 5,
    //     pdfSources: ['pdf-id-1', 'pdf-id-2'] // if answer used PDF context
    //   }
    // }
  ]
};

// Create database structure
function initializeDatabase() {
  const USERS_DIR = path.join(__dirname, 'users');
  const GLOBAL_DATA_DIR = path.join(__dirname, 'data');
  
  // Create main directories
  [USERS_DIR, GLOBAL_DATA_DIR].forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      console.log(`Created directory: ${dir}`);
    }
  });
  
  // Create global data files
  const globalFiles = [
    'sessions.json', // Active user sessions
    'qa.json',      // Global Q&A dataset
    'subjects.json' // Subject categorization data
  ];
  
  globalFiles.forEach(file => {
    const filePath = path.join(__dirname, file);
    if (!fs.existsSync(filePath)) {
      let initialData = {};
      if (file === 'subjects.json') {
        initialData = {
          math: ['algebra', 'calculus', 'geometry', 'statistics'],
          science: ['physics', 'chemistry', 'biology'],
          programming: ['javascript', 'python', 'algorithms', 'data-structures'],
          history: ['world-history', 'ancient-civilizations'],
          literature: ['poetry', 'novels', 'drama']
        };
      }
      fs.writeFileSync(filePath, JSON.stringify(initialData, null, 2));
      console.log(`Created file: ${file}`);
    }
  });
  
  console.log('Database structure initialized successfully!');
}

// Helper function to create user directories
function createUserDirectories(userId) {
  const userDir = path.join(__dirname, 'users', userId);
  const subDirs = [
    'pdfs',           // Store PDF files
    'extracted-text', // Store extracted text files
    'embeddings',     // Store text embeddings for search
    'flashcards',     // Flashcard data
    'bookmarks',      // User bookmarks
    'analytics',      // Detailed analytics
    'chat-history'    // Chat conversation history
  ];
  
  [userDir, ...subDirs.map(dir => path.join(userDir, dir))].forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
  
  // Create user data files
  const userFiles = {
    'profile.json': USER_DATA_STRUCTURE.profile,
    'pdfs.json': USER_DATA_STRUCTURE.pdfs,
    'flashcards.json': USER_DATA_STRUCTURE.flashcards,
    'bookmarks.json': USER_DATA_STRUCTURE.bookmarks,
    'streaks.json': USER_DATA_STRUCTURE.studyStreaks,
    'chat-history.json': USER_DATA_STRUCTURE.chatHistory
  };
  
  Object.entries(userFiles).forEach(([filename, initialData]) => {
    const filePath = path.join(userDir, filename);
    if (!fs.existsSync(filePath)) {
      fs.writeFileSync(filePath, JSON.stringify(initialData, null, 2));
    }
  });
  
  return userDir;
}

// Export functions for use in main server
module.exports = {
  initializeDatabase,
  createUserDirectories,
  USER_DATA_STRUCTURE
};

// Run initialization if called directly
if (require.main === module) {
  initializeDatabase();
}