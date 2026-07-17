import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../context/AuthContext';
import './SignupPage.css';

const CAMEROON_REGIONS = [
  'Adamawa', 'Centre', 'East', 'Far North', 'Littoral',
  'North', 'North-West', 'West', 'South', 'South-West'
];

const ANGLOPHONE_SUBJECTS = [
  'English Language', 'Literature in English', 'Mathematics', 'Additional Mathematics',
  'Physics', 'Chemistry', 'Biology', 'Geography', 'History', 'Economics'
];

const FRANCOPHONE_SUBJECTS = [
  'Francais', 'Mathematiques', 'Physique-Chimie', 'Sciences de la Vie et de la Terre',
  'Histoire-Geographie', 'Anglais', 'Philosophie'
];

function TeacherSignupPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    full_name: '',
    school_name: '',
    school_region: '',
    language_stream: 'anglophone',
    subjects: [],
    class_levels: [],
    email: '',
    phone: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const subjects = formData.language_stream === 'anglophone' ? ANGLOPHONE_SUBJECTS : FRANCOPHONE_SUBJECTS;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubjectToggle = (subject) => {
    setFormData(prev => ({
      ...prev,
      subjects: prev.subjects.includes(subject)
        ? prev.subjects.filter(s => s !== subject)
        : [...prev.subjects, subject]
    }));
  };

  const handleClassToggle = (level) => {
    setFormData(prev => ({
      ...prev,
      class_levels: prev.class_levels.includes(level)
        ? prev.class_levels.filter(l => l !== level)
        : [...prev.class_levels, level]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (formData.subjects.length === 0) {
      setError('Please select at least one subject');
      return;
    }
    if (formData.class_levels.length === 0) {
      setError('Please select at least one class level');
      return;
    }
    
    setIsLoading(true);

    try {
      await axios.post(`${API_URL}/teachers/register`, formData);
      navigate('/login', { state: { message: 'Registration submitted! Your account will be reviewed for approval.' } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    }
    
    setIsLoading(false);
  };

  const classLevels = formData.language_stream === 'anglophone'
    ? ['Form 1', 'Form 2', 'Form 3', 'Form 4', 'Form 5', 'Lower Sixth', 'Upper Sixth']
    : ['6eme', '5eme', '4eme', '3eme', '2nde', '1ere', 'Terminale'];

  return (
    <div className="signup-page">
      <div className="signup-container">
        <div className="signup-header">
          <Link to="/" className="logo">LUMINA CAMEROON</Link>
          <h1>Teacher Registration</h1>
          <p>Join as an educator. Account requires admin approval.</p>
        </div>

        <form onSubmit={handleSubmit} className="signup-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-section">
            <h3>Personal Information</h3>
            <div className="form-group">
              <label>Full Name *</label>
              <input type="text" name="full_name" value={formData.full_name} onChange={handleChange} required />
            </div>
          </div>

          <div className="form-section">
            <h3>School Information</h3>
            <div className="form-group">
              <label>School Name *</label>
              <input type="text" name="school_name" value={formData.school_name} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label>Region *</label>
              <select name="school_region" value={formData.school_region} onChange={handleChange} required>
                <option value="">Select...</option>
                {CAMEROON_REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Language Stream *</label>
              <select name="language_stream" value={formData.language_stream} onChange={handleChange} required>
                <option value="anglophone">Anglophone</option>
                <option value="francophone">Francophone</option>
              </select>
            </div>
          </div>

          <div className="form-section">
            <h3>Subjects Taught *</h3>
            <div className="checkbox-list">
              {subjects.map(subject => (
                <label key={subject} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.subjects.includes(subject)}
                    onChange={() => handleSubjectToggle(subject)}
                  />
                  {subject}
                </label>
              ))}
            </div>
          </div>

          <div className="form-section">
            <h3>Class Levels Taught *</h3>
            <div className="checkbox-list">
              {classLevels.map(level => (
                <label key={level} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.class_levels.includes(level)}
                    onChange={() => handleClassToggle(level)}
                  />
                  {level}
                </label>
              ))}
            </div>
          </div>

          <div className="form-section">
            <h3>Account Details</h3>
            <div className="form-group">
              <label>Email *</label>
              <input type="email" name="email" value={formData.email} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label>Phone *</label>
              <input type="tel" name="phone" value={formData.phone} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label>Password *</label>
              <input type="password" name="password" value={formData.password} onChange={handleChange} minLength={8} required />
            </div>
          </div>

          <button type="submit" className="btn btn-primary btn-full" disabled={isLoading}>
            {isLoading ? 'Submitting...' : 'Submit Registration'}
          </button>
        </form>

        <div className="signup-footer">
          <p>Already have an account? <Link to="/login">Sign In</Link></p>
        </div>
      </div>
    </div>
  );
}

export default TeacherSignupPage;
