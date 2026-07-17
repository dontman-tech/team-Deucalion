import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth, API_URL } from './AuthContext';

const StudentContext = createContext(null);

export function StudentProvider({ children }) {
  const { token } = useAuth();
  const [profile, setProfile] = useState(null);
  const [classes, setClasses] = useState([]);
  const [leaderboardSummary, setLeaderboardSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const config = {
    headers: { Authorization: `Bearer ${token}` }
  };

  useEffect(() => {
    if (token) {
      fetchProfile();
      fetchClasses();
      fetchLeaderboardSummary();
    }
  }, [token]);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API_URL}/students/profile`, config);
      setProfile(response.data);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    }
  };

  const fetchClasses = async () => {
    try {
      const response = await axios.get(`${API_URL}/students/classes`, config);
      setClasses(response.data);
    } catch (error) {
      console.error('Failed to fetch classes:', error);
    }
  };

  const fetchLeaderboardSummary = async () => {
    try {
      const response = await axios.get(`${API_URL}/students/leaderboard/summary`, config);
      setLeaderboardSummary(response.data);
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    }
  };

  const joinClass = async (classCode) => {
    setIsLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/students/join-class`,
        { class_code: classCode },
        config
      );
      await fetchClasses();
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to join class'
      };
    } finally {
      setIsLoading(false);
    }
  };

  const updatePreferences = async (preferences) => {
    try {
      await axios.put(`${API_URL}/students/profile/preferences`, preferences, config);
      await fetchProfile();
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update preferences'
      };
    }
  };

  const value = {
    profile,
    classes,
    leaderboardSummary,
    isLoading,
    fetchProfile,
    fetchClasses,
    fetchLeaderboardSummary,
    joinClass,
    updatePreferences
  };

  return (
    <StudentContext.Provider value={value}>
      {children}
    </StudentContext.Provider>
  );
}

export function useStudent() {
  const context = useContext(StudentContext);
  if (!context) {
    throw new Error('useStudent must be used within a StudentProvider');
  }
  return context;
}
