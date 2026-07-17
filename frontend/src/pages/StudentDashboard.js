import React from 'react';
import { Link } from 'react-router-dom';
import { useStudent } from '../context/StudentContext';
import { useAuth } from '../context/AuthContext';
import LoadingScreen from '../components/LoadingScreen';
import './Dashboard.css';

function StudentDashboard() {
  const { profile, classes, leaderboardSummary, isLoading, error, clearError } = useStudent();
  const { user } = useAuth();

  if (isLoading && !profile) {
    return <LoadingScreen message="Loading your dashboard..." />;
  }

  return (
    <div className="dashboard">
      {error && (
        <div className="error-banner" onClick={clearError}>
          <span>⚠️ {error}</span>
          <button className="dismiss-btn">×</button>
        </div>
      )}

      <div className="dashboard-header">
        <div className="welcome-section">
          <h1>Welcome back, {user?.full_name || 'Student'}!</h1>
          <p className="subtitle">
            {profile?.class_level} • {profile?.language_stream === 'anglophone' ? 'Anglophone' : 'Francophone'} Stream
            {profile?.region && ` • ${profile.region}`}
          </p>
        </div>
        <div className="streak-badge">
          <span className="streak-icon">🔥</span>
          <span className="streak-count">{profile?.streak_days || 0}</span>
          <span className="streak-label">Day Streak</span>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Quick Actions */}
        <div className="card quick-actions">
          <h2>Quick Actions</h2>
          <div className="action-buttons">
            <Link to="/ai-chat" className="action-btn primary">
              <span className="icon">🤖</span>
              <span>Start AI Session</span>
            </Link>
            <Link to="/join-class" className="action-btn">
              <span className="icon">📚</span>
              <span>Join Class</span>
            </Link>
          </div>
        </div>

        {/* My Classes */}
        <div className="card classes-card">
          <h2>My Classes</h2>
          {isLoading ? (
            <div className="loading-inline">
              <span className="spinner-small"></span> Loading classes...
            </div>
          ) : classes.length === 0 ? (
            <div className="empty-state">
              <p>You haven't joined any classes yet.</p>
              <Link to="/join-class" className="btn btn-small btn-primary">Join a Class</Link>
            </div>
          ) : (
            <div className="class-list">
              {classes.map(cls => (
                <div key={cls.id} className="class-item">
                  <div className="class-info">
                    <h3>{cls.subject}</h3>
                    <p>{cls.teacher_name} • {cls.class_level}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Leaderboard Summary */}
        <div className="card leaderboard-card">
          <h2>Leaderboard</h2>
          {leaderboardSummary ? (
            <div className="leaderboard-stats">
              <div className="stat-item">
                <span className="stat-value">{leaderboardSummary.total_points || 0}</span>
                <span className="stat-label">Total Points</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">#{leaderboardSummary.overall_rank || '-'}</span>
                <span className="stat-label">Overall Rank</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">x{leaderboardSummary.streak_multiplier || 1}</span>
                <span className="stat-label">Streak Bonus</span>
              </div>
            </div>
          ) : (
            <p>Complete activities to earn points!</p>
          )}
        </div>

        {/* Student Info Card */}
        <div className="card profile-card">
          <h2>My Profile</h2>
          <div className="profile-info">
            <div className="info-row">
              <span className="label">Lumina ID:</span>
              <span className="value">{profile?.lumina_id || '-'}</span>
            </div>
            <div className="info-row">
              <span className="label">Class Level:</span>
              <span className="value">{profile?.class_level || '-'}</span>
            </div>
            <div className="info-row">
              <span className="label">Performance:</span>
              <span className="value capitalize">{profile?.performance_level || 'average'}</span>
            </div>
          </div>
          <p className="ctc-note">
            <strong>Child Tracking Code:</strong><br />
            <code>{profile?.child_tracking_code || 'Not available'}</code>
            <br />
            <small>Share this with your parents so they can track your progress.</small>
          </p>
        </div>
      </div>
    </div>
  );
}

export default StudentDashboard;
