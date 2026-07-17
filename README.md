# Lumina Cameroon

AI-powered learning companion for Cameroonian students aligned to GCE, BAC, and BEPC curricula.

## Overview

Lumina Cameroon is a comprehensive educational platform that provides:
- **AI Tutoring** with Socratic questioning methodology
- **Curriculum Alignment** to Cameroon national curriculum (GCE Board, OBC, MINEDUB, MINESEC, MINESUP)
- **Multi-language Support** (Anglophone and Francophone streams)
- **Class Management** for teachers with curriculum material uploads
- **Parent Tracking** via Child Tracking Codes
- **Gamified Learning** with leaderboards and badges

## Features

### For Students
- Join classes with codes
- AI tutor with 6 mentor modes (Guide, Explain, Quiz, Writing Coach, Debate, Explore)
- Class-level content locking
- Leaderboard participation
- Study streak tracking

### For Teachers
- Class creation with join codes
- Curriculum material upload system
- Student progress tracking
- Assignment creation
- Student flagging system

### For Parents
- Child Tracking Code linking (max 2 parents per child)
- Progress monitoring dashboard
- Subject performance overview
- Assignment tracking

## Tech Stack

### Backend
- **Python** with FastAPI
- **SQLAlchemy** ORM
- **JWT Authentication**
- **SQLite** (configurable to PostgreSQL)

### Frontend
- **React** with React Router
- **TanStack Query** for data fetching
- **Axios** for API calls

## Project Structure

```
team-Deucalion/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic (Auth, Leaderboard, Lumina AI)
│   │   ├── utils/           # Utilities
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database connection
│   │   └── main.py          # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── public/
│   └── src/
│       ├── components/      # React components
│       ├── context/         # React contexts (Auth, Student, Teacher, Parent)
│       ├── pages/           # Page components
│       └── services/        # API services
└── README.md
```

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user

### Students
- `POST /api/v1/students/register` - Register student
- `GET /api/v1/students/profile` - Get profile
- `POST /api/v1/students/join-class` - Join class with code
- `GET /api/v1/students/classes` - Get enrolled classes
- `GET /api/v1/students/leaderboard/summary` - Get leaderboard

### Teachers
- `POST /api/v1/teachers/register` - Register teacher
- `POST /api/v1/teachers/classes` - Create class
- `GET /api/v1/teachers/classes` - List classes
- `POST /api/v1/teachers/classes/{id}/upload-material` - Upload material
- `POST /api/v1/teachers/assignments` - Create assignment

### Parents
- `POST /api/v1/parents/register` - Register parent with CTC
- `GET /api/v1/parents/dashboard` - Get dashboard
- `GET /api/v1/parents/children/{id}/dashboard` - Child details

### AI Sessions
- `POST /api/v1/ai/sessions/start` - Start session
- `POST /api/v1/ai/sessions/{id}/chat` - Send message
- `POST /api/v1/ai/sessions/{id}/end` - End session

## Curriculum Alignment

### Anglophone Stream
- Primary: Class 1-6
- O Level: Form 1-5 (GCE)
- A Level: Lower Sixth, Upper Sixth

### Francophone Stream
- Primary: SIL, CP, CE1, CE2, CM1, CM2
- College: 6ème, 5ème, 4ème, 3ème (BEPC)
- Lycée: 2nde, 1ère, Terminale (BAC)

## License

Proprietary - All rights reserved.
