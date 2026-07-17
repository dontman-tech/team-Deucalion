import React from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import './LandingPage.css';

function LandingPage() {
  const { isDarkMode, toggleTheme } = useTheme();

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <header className="hero">
        <nav className="navbar">
          <div className="nav-left">
            <div className="logo">LUMINA CAMEROON</div>
          </div>
          <div className="nav-right">
            <button onClick={toggleTheme} className="theme-toggle" title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
              {isDarkMode ? '☀️' : '🌙'}
            </button>
            <Link to="/login" className="nav-link">Login</Link>
            <Link to="/signup/student" className="nav-link btn-primary">Get Started</Link>
            <Link to="/admin/login" className="nav-link admin-link">Admin</Link>
          </div>
        </nav>
        
        <div className="hero-content">
          <h1>Your Personal Learning Companion</h1>
          <p className="tagline">
            World-class education aligned to the Cameroonian curriculum, 
            available in your language, anywhere at any time.
          </p>
          <div className="hero-buttons">
            <Link to="/signup/student" className="btn btn-large btn-primary">
              I'm a Student
            </Link>
            <Link to="/signup/teacher" className="btn btn-large btn-secondary">
              I'm a Teacher
            </Link>
            <Link to="/signup/parent" className="btn btn-large btn-secondary">
              I'm a Parent
            </Link>
          </div>
        </div>
        
        <div className="hero-visual">
          <div className="floating-card card-1">
            <span className="icon">📚</span>
            <span>GCE & BAC Aligned</span>
          </div>
          <div className="floating-card card-2">
            <span className="icon">🎓</span>
            <span>AI Tutor</span>
          </div>
          <div className="floating-card card-3">
            <span className="icon">🌍</span>
            <span>English & Français</span>
          </div>
        </div>
      </header>

      {/* Features Section */}
      <section className="features">
        <h2>Why Choose Lumina Cameroon?</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <div className="feature-icon">📖</div>
            <h3>Curriculum Aligned</h3>
            <p>
              Content perfectly aligned to GCE Board, OBC (BAC), MINEDUB, MINESEC, 
              and MINESUP standards for every class level.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>AI-Powered Tutoring</h3>
            <p>
              Lumina uses the Socratic method to guide you to understanding, 
              not just give you answers. Available 24/7.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🏆</div>
            <h3>Gamified Learning</h3>
            <p>
              Earn points, climb leaderboards, and earn badges while you learn. 
              Study streaks keep you motivated.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">👨‍👩‍👧</div>
            <h3>Parent Tracking</h3>
            <p>
              Parents can monitor progress using Child Tracking Codes. 
              Stay involved in your child's education.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">📱</div>
            <h3>Teacher Resources</h3>
            <p>
              Teachers can upload custom curriculum materials. 
              Lumina uses your materials to teach your students.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">✏️</div>
            <h3>Multiple Modes</h3>
            <p>
              Guide Mode, Explain Mode, Quiz Mode, Writing Coach, 
              Debate Mode, and Explore Mode for every learning need.
            </p>
          </div>
        </div>
      </section>

      {/* Curriculum Section */}
      <section className="curriculum">
        <h2>Complete Cameroon Curriculum Coverage</h2>
        <div className="curriculum-grid">
          <div className="curriculum-column">
            <h3>Anglophone Stream</h3>
            <ul>
              <li>Primary: Class 1-6</li>
              <li>O Level: Form 1-5 (GCE)</li>
              <li>A Level: Lower & Upper Sixth</li>
            </ul>
          </div>
          <div className="curriculum-column">
            <h3>Francophone Stream</h3>
            <ul>
              <li>Primary: SIL → CM2</li>
              <li>College: 6ème → 3ème (BEPC)</li>
              <li>Lycée: 2nde → Terminale (BAC)</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Exam Prep Section */}
      <section className="exam-prep">
        <h2>Exam Preparation Mode</h2>
        <p>
          During GCE, BEPC, and BAC exam season (March-June), Lumina automatically 
          activates enhanced preparation features.
        </p>
        <div className="exam-features">
          <div className="exam-feature">
            <span className="icon">📝</span>
            <span>Past Paper Practice</span>
          </div>
          <div className="exam-feature">
            <span className="icon">⏱️</span>
            <span>Timed Quiz Simulations</span>
          </div>
          <div className="exam-feature">
            <span className="icon">📊</span>
            <span>Weak Topic Identification</span>
          </div>
          <div className="exam-feature">
            <span className="icon">💪</span>
            <span>Stress Management Support</span>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta">
        <h2>Ready to Transform Your Learning?</h2>
        <p>Join thousands of Cameroonian students already using Lumina.</p>
        <Link to="/signup/student" className="btn btn-large btn-primary">
          Start Learning Now - It's Free
        </Link>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-brand">
            <span className="logo">LUMINA CAMEROON</span>
            <p>Every Cameroonian student deserves world-class education.</p>
          </div>
          <div className="footer-links">
            <h4>Quick Links</h4>
            <Link to="/signup/student">Student Sign Up</Link>
            <Link to="/signup/teacher">Teacher Sign Up</Link>
            <Link to="/signup/parent">Parent Sign Up</Link>
            <Link to="/login">Login</Link>
            <Link to="/admin/login">Admin Portal</Link>
          </div>
          <div className="footer-links">
            <h4>Resources</h4>
            <a href="#help">Help Center</a>
            <a href="#contact">Contact Us</a>
            <a href="#privacy">Privacy Policy</a>
            <a href="#terms">Terms of Service</a>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2024 Lumina Cameroon. Built for Cameroon, by Cameroon.</p>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
