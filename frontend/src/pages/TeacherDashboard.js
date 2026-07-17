import React, { useState } from 'react';
import { useTeacher } from '../context/TeacherContext';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

function TeacherDashboard() {
  const { profile, classes, dashboardSummary, createClass, getClassStudents } = useTeacher();
  const { user } = useAuth();
  const [showCreateClass, setShowCreateClass] = useState(false);
  const [selectedClassId, setSelectedClassId] = useState(null);
  const [classStudents, setClassStudents] = useState([]);

  const isApproved = profile?.is_approved;
  const isPending = profile?.approval_status === 'pending';

  const handleViewStudents = async (classId) => {
    setSelectedClassId(classId);
    const result = await getClassStudents(classId);
    if (result.success) {
      setClassStudents(result.data);
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="welcome-section">
          <h1>Welcome, {user?.full_name || 'Teacher'}!</h1>
          <p className="subtitle">
            {profile?.school_name} • {profile?.school_region}
          </p>
        </div>
        <div className="status-badge">
          {isPending && <span className="badge pending">⏳ Pending Approval</span>}
          {isApproved && <span className="badge approved">✓ Verified Teacher</span>}
        </div>
      </div>

      {!isApproved && (
        <div className="card info-card">
          <h2>Account Status</h2>
          <p>
            {isPending 
              ? 'Your account is awaiting admin approval. You currently have read-only access. Once approved, you\'ll be able to create classes, upload materials, and create assignments.'
              : 'Your account is not yet approved. Contact your administrator for assistance.'}
          </p>
        </div>
      )}

      {dashboardSummary?.classes_needing_material > 0 && (
        <div className="card warning-card">
          <h2>📚 Materials Needed</h2>
          <p>{dashboardSummary.message}</p>
          <p>You have {dashboardSummary.classes_needing_material} class(es) without uploaded materials.</p>
        </div>
      )}

      <div className="dashboard-grid">
        {/* Stats */}
        <div className="card stats-card">
          <h2>Overview</h2>
          <div className="stats-grid">
            <div className="stat">
              <span className="stat-value">{dashboardSummary?.total_classes || 0}</span>
              <span className="stat-label">Classes</span>
            </div>
            <div className="stat">
              <span className="stat-value">{dashboardSummary?.total_students || 0}</span>
              <span className="stat-label">Students</span>
            </div>
            <div className="stat">
              <span className="stat-value">{dashboardSummary?.pending_flags || 0}</span>
              <span className="stat-label">Flags</span>
            </div>
          </div>
        </div>

        {/* Classes */}
        <div className="card classes-card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header">
            <h2>My Classes</h2>
            {isApproved && (
              <button onClick={() => setShowCreateClass(true)} className="btn btn-small btn-primary">
                + Create Class
              </button>
            )}
          </div>
          {classes.length === 0 ? (
            <div className="empty-state">
              <p>You haven't created any classes yet.</p>
            </div>
          ) : (
            <div className="class-list">
              {classes.map(cls => (
                <div key={cls.id} className="class-item">
                  <div className="class-info">
                    <h3>{cls.subject}</h3>
                    <p>{cls.class_level} • {cls.student_count} students</p>
                    <code className="class-code">{cls.class_code}</code>
                  </div>
                  <div className="class-actions">
                    <button onClick={() => handleViewStudents(cls.id)} className="btn btn-small">
                      View Students
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Students Panel */}
        {selectedClassId && classStudents.length > 0 && (
          <div className="card students-panel" style={{ gridColumn: 'span 2' }}>
            <div className="card-header">
              <h2>Students in Class</h2>
              <button onClick={() => setSelectedClassId(null)} className="btn btn-small">✕</button>
            </div>
            <table className="students-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Lumina ID</th>
                  <th>Tracking Code</th>
                  <th>Streak</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {classStudents.map(student => (
                  <tr key={student.id}>
                    <td>{student.full_name}</td>
                    <td><code>{student.lumina_id}</code></td>
                    <td><code>{student.child_tracking_code}</code></td>
                    <td>{student.streak_days} days</td>
                    <td>
                      <button className="btn btn-small">Flag</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Class Modal */}
      {showCreateClass && (
        <CreateClassModal
          onClose={() => setShowCreateClass(false)}
          onSubmit={async (data) => {
            await createClass(data);
            setShowCreateClass(false);
          }}
        />
      )}
    </div>
  );
}

function CreateClassModal({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    subject: '',
    class_level: '',
    language_stream: 'anglophone',
    is_permanent: false,
    expires_in_days: 7
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h2>Create New Class</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Subject *</label>
            <input
              type="text"
              value={formData.subject}
              onChange={(e) => setFormData({...formData, subject: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Class Level *</label>
            <input
              type="text"
              value={formData.class_level}
              onChange={(e) => setFormData({...formData, class_level: e.target.value})}
              placeholder="e.g., Form 3"
              required
            />
          </div>
          <div className="form-group">
            <label>Language Stream</label>
            <select
              value={formData.language_stream}
              onChange={(e) => setFormData({...formData, language_stream: e.target.value})}
            >
              <option value="anglophone">Anglophone</option>
              <option value="francophone">Francophone</option>
            </select>
          </div>
          <div className="form-actions">
            <button type="button" onClick={onClose} className="btn">Cancel</button>
            <button type="submit" className="btn btn-primary">Create</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default TeacherDashboard;
