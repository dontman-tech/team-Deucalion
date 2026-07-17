import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../context/AuthContext';
import './SignupPage.css';

const CAMEROON_REGIONS = [
  'Adamawa', 'Centre', 'East', 'Far North', 'Littoral',
  'North', 'North-West', 'West', 'South', 'South-West'
];

const ANGLOPHONE_LEVELS = {
  'Primary': ['Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5', 'Class 6'],
  'O Level': ['Form 1', 'Form 2', 'Form 3', 'Form 4', 'Form 5'],
  'A Level': ['Lower Sixth', 'Upper Sixth']
};

const FRANCOPHONE_LEVELS = {
  'Primary': ['SIL', 'CP', 'CE1', 'CE2', 'CM1', 'CM2'],
  'College': ['6eme', '5eme', '4eme', '3eme'],
  'Lycee': ['2nde', '1ere', 'Terminale']
};

function StudentSignupPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    full_name: '',
    date_of_birth: '',
    gender: '',
    school_name: '',
    region: '',
    language_stream: 'anglophone',
    class_level: '',
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const levels = formData.language_stream === 'anglophone' ? ANGLOPHONE_LEVELS : FRANCOPHONE_LEVELS;
  const flatLevels = Object.values(levels).flat();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Reset class level when stream changes
    if (name === 'language_stream') {
      setFormData(prev => ({ ...prev, class_level: '' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await axios.post(`${API_URL}/students/register`, formData);
      navigate('/login', { state: { message: 'Registration successful! Please login.' } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    }
    
    setIsLoading(false);
  };

  return (
    <div className="signup-page">
      <div className="signup-container">
        <div className="signup-header">
          <Link to="/" className="logo">LUMINA CAMEROON</Link>
          <h1>Student Registration</h1>
          <p>Join thousands of Cameroonian students learning with Lumina</p>
        </div>

        <form onSubmit={handleSubmit} className="signup-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-section">
            <h3>Personal Information</h3>
            <div className="form-row">
              <div className="form-group">
                <label>Full Name *</label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Date of Birth *</label>
                <input
                  type="date"
                  name="date_of_birth"
                  value={formData.date_of_birth}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Gender *</label>
                <select name="gender" value={formData.gender} onChange={handleChange} required>
                  <option value="">Select...</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label>School Name</label>
                <input
                  type="text"
                  name="school_name"
                  value={formData.school_name}
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>Location & Education</h3>
            <div className="form-row">
              <div className="form-group">
                <label>Region *</label>
                <select name="region" value={formData.region} onChange={handleChange} required>
                  <option value="">Select Region...</option>
                  {CAMEROON_REGIONS.map(r => (
                    <option key={r} value={r}>{r}</option>
                  ))}
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
            <div className="form-group">
              <label>Class Level *</label>
              <select name="class_level" value={formData.class_level} onChange={handleChange} required>
                <option value="">Select Class Level...</option>
                {flatLevels.map(level => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-section">
            <h3>Account Details</h3>
            <div className="form-row">
              <div className="form-group">
                <label>Username *</label>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  minLength={3}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password *</label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  minLength={8}
                  required
                />
              </div>
            </div>
          </div>

          <button type="submit" className="btn btn-primary btn-full" disabled={isLoading}>
            {isLoading ? 'Creating Account...' : 'Create Student Account'}
          </button>
        </form>

        <div className="signup-footer">
          <p>Already have an account? <Link to="/login">Sign In</Link></p>
        </div>
      </div>
    </div>
  );
}

export default StudentSignupPage;
