import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../context/AuthContext';
import './SignupPage.css';

function ParentSignupPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    email: '',
    password: '',
    child_tracking_code: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await axios.post(`${API_URL}/parents/register`, formData);
      navigate('/login', { state: { message: 'Parent account created! You can add more children after logging in.' } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    }
    
    setIsLoading(false);
  };

  return (
    <div className="signup-page">
      <div className="signup-container">
        <div className="signup-header">
          <Link to="/" className="logo">LUMINA CAMEROON</Link>
          <h1>Parent Registration</h1>
          <p>Track your child's learning progress</p>
        </div>

        <form onSubmit={handleSubmit} className="signup-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-section">
            <h3>Your Information</h3>
            <div className="form-group">
              <label>Full Name *</label>
              <input type="text" name="full_name" value={formData.full_name} onChange={handleChange} required />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Phone *</label>
                <input type="tel" name="phone" value={formData.phone} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Email *</label>
                <input type="email" name="email" value={formData.email} onChange={handleChange} required />
              </div>
            </div>
            <div className="form-group">
              <label>Password *</label>
              <input type="password" name="password" value={formData.password} onChange={handleChange} minLength={8} required />
            </div>
          </div>

          <div className="form-section">
            <h3>Link Your Child</h3>
            <p className="section-note">Enter your child's Child Tracking Code (CTC) to link their account.</p>
            <div className="form-group">
              <label>Child Tracking Code *</label>
              <input
                type="text"
                name="child_tracking_code"
                value={formData.child_tracking_code}
                onChange={handleChange}
                placeholder="CTC-XXXXXX"
                required
              />
            </div>
            <p className="help-text">
              Get this code from your child's profile or ask their teacher.
              Maximum 2 parent accounts can be linked per child.
            </p>
          </div>

          <button type="submit" className="btn btn-primary btn-full" disabled={isLoading}>
            {isLoading ? 'Creating Account...' : 'Create Parent Account'}
          </button>
        </form>

        <div className="signup-footer">
          <p>Already have an account? <Link to="/login">Sign In</Link></p>
        </div>
      </div>
    </div>
  );
}

export default ParentSignupPage;
