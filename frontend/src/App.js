import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { StudentProvider } from './context/StudentContext';
import { TeacherProvider } from './context/TeacherContext';
import { ParentProvider } from './context/ParentContext';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import StudentSignupPage from './pages/StudentSignupPage';
import TeacherSignupPage from './pages/TeacherSignupPage';
import ParentSignupPage from './pages/ParentSignupPage';
import StudentDashboard from './pages/StudentDashboard';
import TeacherDashboard from './pages/TeacherDashboard';
import ParentDashboard from './pages/ParentDashboard';
import AIChatPage from './pages/AIChatPage';
import JoinClassPage from './pages/JoinClassPage';

// Components
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
});

function AppRoutes() {
  const { user, isAuthenticated } = useAuth();

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup/student" element={<StudentSignupPage />} />
      <Route path="/signup/teacher" element={<TeacherSignupPage />} />
      <Route path="/signup/parent" element={<ParentSignupPage />} />

      {/* Protected Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          {/* Student Routes */}
          <Route path="/student/*" element={
            <StudentProvider>
              <StudentDashboard />
            </StudentProvider>
          } />
          
          {/* Teacher Routes */}
          <Route path="/teacher/*" element={
            <TeacherProvider>
              <TeacherDashboard />
            </TeacherProvider>
          } />
          
          {/* Parent Routes */}
          <Route path="/parent/*" element={
            <ParentProvider>
              <ParentDashboard />
            </ParentProvider>
          } />
          
          {/* Common Routes */}
          <Route path="/ai-chat" element={<AIChatPage />} />
          <Route path="/join-class" element={<JoinClassPage />} />
        </Route>
      </Route>

      {/* Redirects */}
      <Route path="*" element={
        isAuthenticated ? (
          <Navigate to={`/${user?.userType}`} replace />
        ) : (
          <Navigate to="/login" replace />
        )
      } />
    </Routes>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <AppRoutes />
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
