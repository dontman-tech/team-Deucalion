import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../context/AuthContext';
import './Dashboard.css';

const CAMEROON_REGIONS = [
  'Adamawa', 'Centre', 'East', 'Far North', 'Littoral',
  'North', 'North-West', 'West', 'South', 'South-West'
];

function AdminDashboard() {
  const navigate = useNavigate();
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
    try {
      const [statsRes, schoolsRes, teachersRes] = await Promise.all([
        axios.get(`${API_URL}/admin/stats`),
        axios.get(`${API_URL}/admin/schools`),
        axios.get(`${API_URL}/admin/pending-teachers`)
      ]);
      setStats(statsRes.data);
      setSchools(schoolsRes.data);
      setPendingTeachers(teachersRes.data);
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError('Failed to load dashboard data');
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
    
    try {
      await axios.post(`${API_URL}/admin/schools`, newSchool);
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
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add school');
    }
  };

  const handleToggleSchool = async (schoolId) => {
    try {
      await axios.put(`${API_URL}/admin/schools/${schoolId}/toggle-active`);
      fetchData();
    } catch (err) {
      setError('Failed to update school');
    }
  };

  const handleDeleteSchool = async (schoolId) => {
    if (!window.confirm('Are you sure you want to delete this school?')) return;
    try {
      await axios.delete(`${API_URL}/admin/schools/${schoolId}`);
      fetchData();
    } catch (err) {
      setError('Failed to delete school');
    }
  };

  const handleApproveTeacher = async (teacherId) => {
    try {
      await axios.post(`${API_URL}/admin/teachers/${teacherId}/approve`);
      fetchData();
    } catch (err) {
      setError('Failed to approve teacher');
    }
  };

  const handleRejectTeacher = async (teacherId) => {
    try {
      await axios.post(`${API_URL}/admin/teachers/${teacherId}/reject`);
      fetchData();
    } catch (err) {
      setError('Failed to reject teacher');
    }
  };

  if (loading) {
    return <div className="dashboard-loading">Loading...</div>;
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Admin Dashboard</h1>
          <p>Welcome, {localStorage.getItem('admin_username')}</p>
        </div>
        <div className="header-right">
          <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Students</h3>
          <p className="stat-value">{stats?.total_students || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Approved Teachers</h3>
          <p className="stat-value">{stats?.approved_teachers || 0}</p>
        </div>
        <div className="stat-card pending">
          <h3>Pending Teachers</h3>
          <p className="stat-value">{stats?.pending_teachers || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Total Parents</h3>
          <p className="stat-value">{stats?.total_parents || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Total Schools</h3>
          <p className="stat-value">{stats?.total_schools || 0}</p>
        </div>
      </div>

      {/* Schools Section */}
      <div className="dashboard-section">
        <div className="section-header">
          <h2>Schools Management</h2>
          <button onClick={() => setShowAddSchool(!showAddSchool)} className="btn btn-primary">
            {showAddSchool ? 'Cancel' : '+ Add School'}
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
                    <option value="">Select...</option>
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
                  />
                </div>
                <div className="form-group">
                  <label>Contact Phone</label>
                  <input
                    type="tel"
                    value={newSchool.contact_phone}
                    onChange={(e) => setNewSchool({...newSchool, contact_phone: e.target.value})}
                  />
                </div>
              </div>
              <button type="submit" className="btn btn-primary">Add School</button>
            </form>
          </div>
        )}

        <div className="schools-list">
          {schools.length === 0 ? (
            <p className="empty-state">No schools registered yet. Add a school to get started.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>School Name</th>
                  <th>Region</th>
                  <th>Stream</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {schools.map(school => (
                  <tr key={school.id}>
                    <td>{school.name}</td>
                    <td>{school.region}</td>
                    <td>{school.language_stream}</td>
                    <td>
                      <span className={`status-badge ${school.is_active ? 'active' : 'inactive'}`}>
                        {school.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => handleToggleSchool(school.id)}
                        className="btn btn-small"
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
      </div>

      {/* Pending Teachers Section */}
      <div className="dashboard-section">
        <div className="section-header">
          <h2>Pending Teacher Approvals</h2>
        </div>

        {pendingTeachers.length === 0 ? (
          <p className="empty-state">No pending teacher approvals.</p>
        ) : (
          <div className="teachers-list">
            {pendingTeachers.map(teacher => (
              <div key={teacher.id} className="teacher-card">
                <div className="teacher-info">
                  <h4>{teacher.full_name}</h4>
                  <p><strong>Email:</strong> {teacher.email}</p>
                  <p><strong>Phone:</strong> {teacher.phone}</p>
                  <p><strong>School:</strong> {teacher.school_name} ({teacher.school_region})</p>
                  <p><strong>Subjects:</strong> {teacher.subjects?.join(', ')}</p>
                  <p><strong>Class Levels:</strong> {teacher.class_levels?.join(', ')}</p>
                </div>
                <div className="teacher-actions">
                  <button
                    onClick={() => handleApproveTeacher(teacher.id)}
                    className="btn btn-primary"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleRejectTeacher(teacher.id)}
                    className="btn btn-danger"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default AdminDashboard;
