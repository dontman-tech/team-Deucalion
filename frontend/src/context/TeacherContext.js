import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth, API_URL } from './AuthContext';

const TeacherContext = createContext(null);

export function TeacherProvider({ children }) {
  const { token } = useAuth();
  const [profile, setProfile] = useState(null);
  const [classes, setClasses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [dashboardSummary, setDashboardSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const config = {
    headers: { Authorization: `Bearer ${token}` }
  };

  useEffect(() => {
    if (token) {
      fetchProfile();
      fetchClasses();
      fetchAssignments();
      fetchDashboardSummary();
    }
  }, [token]);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API_URL}/teachers/profile`, config);
      setProfile(response.data);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    }
  };

  const fetchClasses = async () => {
    try {
      const response = await axios.get(`${API_URL}/teachers/classes`, config);
      setClasses(response.data);
    } catch (error) {
      console.error('Failed to fetch classes:', error);
    }
  };

  const fetchAssignments = async () => {
    try {
      const response = await axios.get(`${API_URL}/teachers/assignments`, config);
      setAssignments(response.data);
    } catch (error) {
      console.error('Failed to fetch assignments:', error);
    }
  };

  const fetchDashboardSummary = async () => {
    try {
      const response = await axios.get(`${API_URL}/teachers/dashboard/summary`, config);
      setDashboardSummary(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    }
  };

  const createClass = async (classData) => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${API_URL}/teachers/classes`, classData, config);
      await fetchClasses();
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to create class'
      };
    } finally {
      setIsLoading(false);
    }
  };

  const getClassStudents = async (classId) => {
    try {
      const response = await axios.get(`${API_URL}/teachers/classes/${classId}/students`, config);
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch students'
      };
    }
  };

  const createAssignment = async (assignmentData) => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${API_URL}/teachers/assignments`, assignmentData, config);
      await fetchAssignments();
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to create assignment'
      };
    } finally {
      setIsLoading(false);
    }
  };

  const flagStudent = async (studentId, flagType, reason) => {
    try {
      await axios.post(
        `${API_URL}/teachers/students/${studentId}/flag`,
        null,
        { params: { flag_type: flagType, reason }, ...config }
      );
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to flag student'
      };
    }
  };

  const value = {
    profile,
    classes,
    assignments,
    dashboardSummary,
    isLoading,
    fetchProfile,
    fetchClasses,
    fetchAssignments,
    fetchDashboardSummary,
    createClass,
    getClassStudents,
    createAssignment,
    flagStudent
  };

  return (
    <TeacherContext.Provider value={value}>
      {children}
    </TeacherContext.Provider>
  );
}

export function useTeacher() {
  const context = useContext(TeacherContext);
  if (!context) {
    throw new Error('useTeacher must be used within a TeacherProvider');
  }
  return context;
}
