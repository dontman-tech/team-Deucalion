import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../context/AuthContext';
import LoadingScreen from '../components/LoadingScreen';
import './Dashboard.css';
import './AdminDashboard.css';

const CAMEROON_REGIONS = [
  'Adamawa', 'Centre', 'East', 'Far North', 'Littoral',
  'North', 'North-West', 'West', 'South', 'South-West'
];

function AdminDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [schools, setSchools] = useState([]);
  const [pendingTeachers, setPendingTeachers] = useState([]);
  const [showAddSchool, setShowAddSchool] = useState(false);
  const [newSchool, setNewSchool] = useState({
    name: '',
    region: '',
    language_stream: 'anglophone',
    address: '',
    contact_email: '',
    contact_phone: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true);

  const isAdmin = localStorage.getItem('admin_token');

  useEffect(() => {
    if (!isAdmin) {
      navigate('/admin/login');
      return;
    }
    fetchData();
  }, [isAdmin, navigate]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [statsRes, schoolsRes, teachersRes] = await Promise.all([
        axios.get(`${API_URL}/admin/stats`),
        axios.get(`${API_URL}/admin/schools`),
        axios.get(`${API_URL}/admin/pending-teachers`)
      ]);
      setStats(statsRes.data);
      setSchools(schoolsRes.data || []);
      setPendingTeachers(teachersRes.data || []);
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
    }
    setLoading(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_username');
    navigate('/admin/login');
  };

  const handleAddSchool = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    try {
      await axios.post(`${API_URL}/admin/schools`, newSchool);
      setSuccess('School added successfully!');
      setShowAddSchool(false);
      setNewSchool({
        name: '',
        region: '',
        language_stream: 'anglophone',
        address: '',
        contact_email: '',
        contact_phone: ''
      });
      fetchData();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add school');
    }
  };

  const handleToggleSchool = async (schoolId) => {
    try {
      await axios.put(`${API_URL}/admin/schools/${schoolId}/toggle-active`);
      setSuccess('School status updated!');
      fetchData();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to update school');
    }
  };

  const handleDeleteSchool = async (schoolId) => {
    if (!window.confirm('Are you sure you want to delete this school?')) return;
    try {
      await axios.delete(`${API_URL}/admin/schools/${schoolId}`);
      setSuccess('School deleted successfully!');
      fetchData();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to delete school');
    }
  };

  const handleApproveTeacher = async (teacherId) => {
    try {
      await axios.post(`${API_URL}/admin/teachers/${teacherId}/approve`);
      setSuccess('Teacher approved successfully!');
      fetchData();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to approve teacher');
    }
  };

  const handleRejectTeacher = async (teacherId) => {
    if (!window.confirm('Are you sure you want to reject this teacher?')) return;
    try {
      await axios.post(`${API_URL}/admin/teachers/${teacherId}/reject`);
      setSuccess('Teacher rejected successfully!');
      fetchData();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to reject teacher');
    }
  };

  if (loading) {
    return <LoadingScreen message="Loading admin dashboard..." />;
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-sidebar">
        <div className="admin-logo">LUMINA ADMIN</div>
        <nav className="admin-nav">
          <button 
            className={`admin-nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            📊 Overview
          </button>
          <button 
            className={`admin-nav-item ${activeTab === 'schools' ? 'active' : ''}`}
            onClick={() => setActiveTab('schools')}
          >
            🏫 Schools
            {schools.length > 0 && <span className="badge">{schools.length}</span>}
          </button>
          <button 
            className={`admin-nav-item ${activeTab === 'teachers' ? 'active' : ''}`}
            onClick={() => setActiveTab('teachers')}
          >
            👨‍🏫 Teachers
            {pendingTeachers.length > 0 && <span className="badge warning">{pendingTeachers.length}</span>}
          </button>
        </nav>
        <button onClick={handleLogout} className="admin-logout">Logout</button>
      </div>

      <div className="admin-content">
        <div className="admin-header">
          <h1>Welcome, {localStorage.getItem('admin_username')}</h1>
          <p>Platform Management Dashboard</p>
        </div>

        {error && (
          <div className="admin-alert error" onClick={() => setError('')}>
            <span>⚠️ {error}</span>
            <button className="dismiss-btn">×</button>
          </div>
        )}

        {success && (
          <div className="admin-alert success" onClick={() => setSuccess('')}>
            <span>✓ {success}</span>
            <button className="dismiss-btn">×</button>
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="admin-section">
            <h2>Platform Statistics</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">👨‍🎓</div>
                <div className="stat-info">
                  <h3>Total Students</h3>
                  <p className="stat-value">{stats?.total_students || 0}</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">👨‍🏫</div>
                <div className="stat-info">
                  <h3>Total Teachers</h3>
                  <p className="stat-value">{stats?.total_teachers || 0}</p>
                </div>
              </div>
              <div className="stat-card approved">
                <div className="stat-icon">✓</div>
                <div className="stat-info">
                  <h3>Approved Teachers</h3>
                  <p className="stat-value">{stats?.approved_teachers || 0}</p>
                </div>
              </div>
              <div className="stat-card pending">
                <div className="stat-icon">⏳</div>
                <div className="stat-info">
                  <h3>Pending Approval</h3>
                  <p className="stat-value">{stats?.pending_teachers || 0}</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">👨‍👩‍👧</div>
                <div className="stat-info">
                  <h3>Total Parents</h3>
                  <p className="stat-value">{stats?.total_parents || 0}</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🏫</div>
                <div className="stat-info">
                  <h3>Schools</h3>
                  <p className="stat-value">{stats?.total_schools || 0}</p>
                </div>
              </div>
            </div>

            {pendingTeachers.length > 0 && (
              <div className="quick-actions">
                <h3>⚠️ Pending Actions</h3>
                <p>You have {pendingTeachers.length} teacher(s) waiting for approval.</p>
                <button className="btn btn-primary" onClick={() => setActiveTab('teachers')}>
                  Review Teachers
                </button>
              </div>
            )}
          </div>
        )}

        {/* Schools Tab */}
        {activeTab === 'schools' && (
          <div className="admin-section">
            <div className="section-actions">
              <h2>Schools Management</h2>
              <button onClick={() => setShowAddSchool(!showAddSchool)} className="btn btn-primary">
                {showAddSchool ? '✕ Cancel' : '+ Add School'}
              </button>
            </div>

            {showAddSchool && (
              <div className="form-card">
                <h3>Add New School</h3>
                <form onSubmit={handleAddSchool}>
                  <div className="form-row">
                    <div className="form-group">
                      <label>School Name *</label>
                      <input
                        type="text"
                        value={newSchool.name}
                        onChange={(e) => setNewSchool({...newSchool, name: e.target.value})}
                        placeholder="e.g., Government Secondary School Bamenda"
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Region *</label>
                      <select
                        value={newSchool.region}
                        onChange={(e) => setNewSchool({...newSchool, region: e.target.value})}
                        required
                      >
                        <option value="">Select Region...</option>
                        {CAMEROON_REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
                      </select>
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Language Stream *</label>
                      <select
                        value={newSchool.language_stream}
                        onChange={(e) => setNewSchool({...newSchool, language_stream: e.target.value})}
                        required
                      >
                        <option value="anglophone">Anglophone</option>
                        <option value="francophone">Francophone</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Address</label>
                      <input
                        type="text"
                        value={newSchool.address}
                        onChange={(e) => setNewSchool({...newSchool, address: e.target.value})}
                        placeholder="Physical address"
                      />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Contact Email</label>
                      <input
                        type="email"
                        value={newSchool.contact_email}
                        onChange={(e) => setNewSchool({...newSchool, contact_email: e.target.value})}
                        placeholder="school@email.com"
                      />
                    </div>
                    <div className="form-group">
                      <label>Contact Phone</label>
                      <input
                        type="tel"
                        value={newSchool.contact_phone}
                        onChange={(e) => setNewSchool({...newSchool, contact_phone: e.target.value})}
                        placeholder="+237 6XX XXX XXX"
                      />
                    </div>
                  </div>
                  <button type="submit" className="btn btn-primary">Add School</button>
                </form>
              </div>
            )}

            {schools.length === 0 ? (
              <div className="empty-state">
                <p>No schools registered yet.</p>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>School Name</th>
                    <th>Region</th>
                    <th>Stream</th>
                    <th>Contact</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {schools.map(school => (
                    <tr key={school.id}>
                      <td><strong>{school.name}</strong></td>
                      <td>{school.region}</td>
                      <td>
                        <span className={`stream-badge ${school.language_stream}`}>
                          {school.language_stream === 'anglophone' ? '🇬🇧' : '🇫🇷'} 
                          {school.language_stream}
                        </span>
                      </td>
                      <td>{school.contact_email || school.contact_phone || '-'}</td>
                      <td>
                        <span className={`status-badge ${school.is_active ? 'active' : 'inactive'}`}>
                          {school.is_active ? '✓ Active' : '✕ Inactive'}
                        </span>
                      </td>
                      <td className="actions-cell">
                        <button
                          onClick={() => handleToggleSchool(school.id)}
                          className={`btn btn-small ${school.is_active ? '' : 'btn-success'}`}
                        >
                          {school.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                          onClick={() => handleDeleteSchool(school.id)}
                          className="btn btn-small btn-danger"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Teachers Tab */}
        {activeTab === 'teachers' && (
          <div className="admin-section">
            <h2>Teacher Approvals</h2>
            
            {pendingTeachers.length === 0 ? (
              <div className="empty-state success">
                <p>✓ No pending teacher approvals. All caught up!</p>
              </div>
            ) : (
              <div className="teachers-grid">
                {pendingTeachers.map(teacher => (
                  <div key={teacher.id} className="teacher-card">
                    <div className="teacher-header">
                      <div className="teacher-avatar">{teacher.full_name?.charAt(0) || 'T'}</div>
                      <div className="teacher-name">
                        <h4>{teacher.full_name}</h4>
                        <span className="approval-badge">Pending</span>
                      </div>
                    </div>
                    <div className="teacher-details">
                      <p><strong>Email:</strong> {teacher.email}</p>
                      <p><strong>Phone:</strong> {teacher.phone}</p>
                      <p><strong>School:</strong> {teacher.school_name}</p>
                      <p><strong>Region:</strong> {teacher.school_region}</p>
                      <p><strong>Stream:</strong> {teacher.language_stream}</p>
                    </div>
                    {teacher.subjects?.length > 0 && (
                      <div className="teacher-subjects">
                        <strong>Subjects:</strong>
                        <div className="subject-tags">
                          {teacher.subjects.map((s, i) => (
                            <span key={i} className="subject-tag">{s}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {teacher.class_levels?.length > 0 && (
                      <div className="teacher-levels">
                        <strong>Class Levels:</strong>
                        <span>{teacher.class_levels.join(', ')}</span>
                      </div>
                    )}
                    <div className="teacher-card-actions">
                      <button
                        onClick={() => handleApproveTeacher(teacher.id)}
                        className="btn btn-success btn-full"
                      >
                        ✓ Approve
                      </button>
                      <button
                        onClick={() => handleRejectTeacher(teacher.id)}
                        className="btn btn-danger btn-full"
                      >
                        ✕ Reject
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default AdminDashboard;
