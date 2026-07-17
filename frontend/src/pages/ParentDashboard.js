import React, { useState } from 'react';
import { useParent } from '../context/ParentContext';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

function ParentDashboard() {
  const { dashboard, activeChildId, childDashboard, childProgress, childAssignments, selectChild, addChild } = useParent();
  const { user } = useAuth();
  const [showAddChild, setShowAddChild] = useState(false);
  const [newChildCode, setNewChildCode] = useState('');
  const [error, setError] = useState('');

  const handleAddChild = async (e) => {
    e.preventDefault();
    setError('');
    const result = await addChild(newChildCode);
    if (result.success) {
      setNewChildCode('');
      setShowAddChild(false);
    } else {
      setError(result.error);
    }
  };

  const activeChild = dashboard?.children?.find(c => c.id === activeChildId);

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="welcome-section">
          <h1>Welcome, {user?.full_name || 'Parent'}!</h1>
          <p className="subtitle">Monitoring {dashboard?.children?.length || 0} child(ren)</p>
        </div>
      </div>

      {/* Children Cards */}
      <div className="children-cards">
        {dashboard?.children?.map(child => (
          <div
            key={child.id}
            className={`child-card ${child.id === activeChildId ? 'active' : ''}`}
            onClick={() => selectChild(child.id)}
          >
            <div className="child-avatar">
              {child.full_name.charAt(0)}
            </div>
            <div className="child-info">
              <h3>{child.full_name}</h3>
              <p>{child.class_level} • {child.language_stream}</p>
              <span className={`status ${child.is_active_recently ? 'active' : 'inactive'}`}>
                {child.is_active_recently ? 'Active recently' : 'Not active'}
              </span>
            </div>
          </div>
        ))}
        
        <div className="add-child-card" onClick={() => setShowAddChild(true)}>
          <span className="add-icon">+</span>
          <span>Add Child</span>
        </div>
      </div>

      {/* Child Dashboard */}
      {activeChild && childDashboard && (
        <div className="dashboard-grid">
          {/* Progress Overview */}
          <div className="card progress-card">
            <h2>📊 Progress Overview</h2>
            <div className="progress-stats">
              <div className="stat">
                <span className="stat-value">{childDashboard.study_time_this_week}</span>
                <span className="stat-label">Minutes This Week</span>
              </div>
              <div className="stat">
                <span className="stat-value">{childDashboard.ai_sessions_this_week}</span>
                <span className="stat-label">AI Sessions</span>
              </div>
              <div className="stat">
                <span className="stat-value">{childDashboard.current_streak}</span>
                <span className="stat-label">Day Streak 🔥</span>
              </div>
              <div className="stat">
                <span className="stat-value">#{childDashboard.current_class_rank || '-'}</span>
                <span className="stat-label">Class Rank</span>
              </div>
            </div>
          </div>

          {/* Assignments */}
          <div className="card assignments-card">
            <h2>📝 Assignments</h2>
            <div className="assignment-stats">
              <div className="stat">
                <span className="stat-value">{childDashboard.assignments_submitted}</span>
                <span className="stat-label">Submitted</span>
              </div>
              <div className="stat">
                <span className="stat-value">{childDashboard.assignments_total}</span>
                <span className="stat-label">Total</span>
              </div>
            </div>
          </div>

          {/* Subject Performance */}
          <div className="card performance-card">
            <h2>📚 Subject Performance</h2>
            {childDashboard.subject_performance?.map((subject, index) => (
              <div key={index} className="subject-row">
                <span className="subject-name">{subject.subject}</span>
                <div className="progress-bar">
                  <div
                    className={`progress-fill ${subject.status}`}
                    style={{ width: `${subject.percentage}%` }}
                  />
                </div>
                <span className="subject-percentage">{subject.percentage}%</span>
              </div>
            ))}
          </div>

          {/* AI Summary */}
          <div className="card summary-card">
            <h2>💡 Lumina's Summary</h2>
            <p className="ai-summary">{childDashboard.ai_summary}</p>
            <div className="recommendation">
              <strong>Recommendation:</strong>
              <p>{childDashboard.recommended_action}</p>
            </div>
          </div>

          {/* Upcoming Deadlines */}
          {childDashboard.upcoming_deadlines?.length > 0 && (
            <div className="card deadlines-card">
              <h2>📅 Upcoming Deadlines</h2>
              <ul className="deadlines-list">
                {childDashboard.upcoming_deadlines.map((deadline, index) => (
                  <li key={index}>
                    <strong>{deadline.title}</strong>
                    <span>{deadline.subject} • Due: {new Date(deadline.due_date).toLocaleDateString()}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Add Child Modal */}
      {showAddChild && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Add Child</h2>
            <p>Enter your child's Child Tracking Code (CTC) to link their account.</p>
            {error && <div className="error-message">{error}</div>}
            <form onSubmit={handleAddChild}>
              <div className="form-group">
                <label>Child Tracking Code</label>
                <input
                  type="text"
                  value={newChildCode}
                  onChange={(e) => setNewChildCode(e.target.value.toUpperCase())}
                  placeholder="CTC-XXXXXX"
                  required
                />
              </div>
              <div className="form-actions">
                <button type="button" onClick={() => setShowAddChild(false)} className="btn">Cancel</button>
                <button type="submit" className="btn btn-primary">Add Child</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default ParentDashboard;
