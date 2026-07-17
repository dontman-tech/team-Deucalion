import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useStudent } from '../context/StudentContext';
import './JoinClassPage.css';

function JoinClassPage() {
  const navigate = useNavigate();
  const { joinClass, isLoading } = useStudent();
  const [classCode, setClassCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!classCode.trim()) {
      setError('Please enter a class code');
      return;
    }

    const result = await joinClass(classCode.trim().toUpperCase());
    
    if (result.success) {
      setSuccess(`Successfully joined ${result.data.subject} class!`);
      setTimeout(() => navigate('/student'), 2000);
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="join-class-page">
      <div className="join-class-container">
        <Link to="/student" className="back-link">← Back to Dashboard</Link>
        
        <div className="join-card">
          <div className="card-icon">📚</div>
          <h1>Join a Class</h1>
          <p>Enter the class code provided by your teacher to join their class.</p>

          <form onSubmit={handleSubmit}>
            {error && <div className="error-message">{error}</div>}
            {success && <div className="success-message">{success}</div>}
            
            <div className="form-group">
              <label>Class Code</label>
              <input
                type="text"
                value={classCode}
                onChange={(e) => setClassCode(e.target.value.toUpperCase())}
                placeholder="e.g., MATH-2025-39471"
                autoFocus
              />
            </div>

            <button type="submit" className="join-btn" disabled={isLoading}>
              {isLoading ? 'Joining...' : 'Join Class'}
            </button>
          </form>

          <div className="help-text">
            <p>Don't have a class code?</p>
            <p>Ask your teacher for the code. Codes expire after 7 days unless set as permanent.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default JoinClassPage;
