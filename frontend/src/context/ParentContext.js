import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth, API_URL } from './AuthContext';

const ParentContext = createContext(null);

export function ParentProvider({ children }) {
  const { token } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [activeChildId, setActiveChildId] = useState(null);
  const [childDashboard, setChildDashboard] = useState(null);
  const [childProgress, setChildProgress] = useState(null);
  const [childAssignments, setChildAssignments] = useState([]);
  const [childLeaderboard, setChildLeaderboard] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const config = {
    headers: { Authorization: `Bearer ${token}` }
  };

  useEffect(() => {
    if (token) {
      fetchDashboard();
    }
  }, [token]);

  useEffect(() => {
    if (activeChildId && token) {
      fetchChildDashboard(activeChildId);
      fetchChildProgress(activeChildId);
      fetchChildAssignments(activeChildId);
      fetchChildLeaderboard(activeChildId);
    }
  }, [activeChildId, token]);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API_URL}/parents/dashboard`, config);
      setDashboard(response.data);
      
      // Set first child as active if none selected
      if (!activeChildId && response.data.children?.length > 0) {
        setActiveChildId(response.data.children[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    }
  };

  const fetchChildDashboard = async (childId) => {
    try {
      const response = await axios.get(`${API_URL}/parents/children/${childId}/dashboard`, config);
      setChildDashboard(response.data);
    } catch (error) {
      console.error('Failed to fetch child dashboard:', error);
    }
  };

  const fetchChildProgress = async (childId) => {
    try {
      const response = await axios.get(`${API_URL}/parents/children/${childId}/progress`, config);
      setChildProgress(response.data);
    } catch (error) {
      console.error('Failed to fetch child progress:', error);
    }
  };

  const fetchChildAssignments = async (childId) => {
    try {
      const response = await axios.get(`${API_URL}/parents/children/${childId}/assignments`, config);
      setChildAssignments(response.data.assignments || []);
    } catch (error) {
      console.error('Failed to fetch child assignments:', error);
    }
  };

  const fetchChildLeaderboard = async (childId) => {
    try {
      const response = await axios.get(
        `${API_URL}/parents/children/${childId}/leaderboard`,
        config
      );
      setChildLeaderboard(response.data);
    } catch (error) {
      console.error('Failed to fetch child leaderboard:', error);
    }
  };

  const addChild = async (childTrackingCode) => {
    setIsLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/parents/children/add`,
        null,
        { params: { child_tracking_code: childTrackingCode }, ...config }
      );
      await fetchDashboard();
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to add child'
      };
    } finally {
      setIsLoading(false);
    }
  };

  const selectChild = (childId) => {
    setActiveChildId(childId);
  };

  const value = {
    dashboard,
    activeChildId,
    childDashboard,
    childProgress,
    childAssignments,
    childLeaderboard,
    isLoading,
    fetchDashboard,
    fetchChildDashboard,
    fetchChildProgress,
    fetchChildAssignments,
    fetchChildLeaderboard,
    addChild,
    selectChild
  };

  return (
    <ParentContext.Provider value={value}>
      {children}
    </ParentContext.Provider>
  );
}

export function useParent() {
  const context = useContext(ParentContext);
  if (!context) {
    throw new Error('useParent must be used within a ParentProvider');
  }
  return context;
}
