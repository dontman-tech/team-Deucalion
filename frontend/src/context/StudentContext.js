import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth, API_URL } from './AuthContext';

const StudentContext = createContext(null);

export function StudentProvider({ children }) {
  const { token } = useAuth();
  const [profile, setProfile] = useState(null);
  const [classes, setClasses] = useState([]);
  const [leaderboardSummary, setLeaderboardSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchProfile = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_URL}/students/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfile(response.data);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      setError(error.response?.data?.detail || 'Failed to load profile');
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  const fetchClasses = useCallback(async () => {
    if (!token) return;
    setError(null);
    try {
      const response = await axios.get(`${API_URL}/students/classes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setClasses(response.data || []);
    } catch (error) {
      console.error('Failed to fetch classes:', error);
      setError(error.response?.data?.detail || 'Failed to load classes');
    }
  }, [token]);

  const fetchLeaderboardSummary = useCallback(async () => {
    if (!token) return;
    try {
      const response = await axios.get(`${API_URL}/students/leaderboard/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLeaderboardSummary(response.data);
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchProfile();
      fetchClasses();
      fetchLeaderboardSummary();
    }
  }, [token, fetchProfile, fetchClasses, fetchLeaderboardSummary]);

  const joinClass = async (classCode) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${API_URL}/students/join-class`,
        { class_code: classCode },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await fetchClasses();
      return { success: true, data: response.data };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to join class';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setIsLoading(false);
    }
  };

  const updatePreferences = async (preferences) => {
    try {
      await axios.put(
        `${API_URL}/students/profile/preferences`,
        preferences,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await fetchProfile();
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update preferences'
      };
    }
  };

  const clearError = () => setError(null);

  const value = {
    profile,
    classes,
    leaderboardSummary,
    isLoading,
    error,
    fetchProfile,
    fetchClasses,
    fetchLeaderboardSummary,
    joinClass,
    updatePreferences,
    clearError
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
