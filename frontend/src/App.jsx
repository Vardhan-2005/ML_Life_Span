import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import api from './api/api';
import './styles/App.css'

import Login from './pages/Login.jsx'
import Signup from './pages/Signup.jsx'
import Dashboard from './pages/Dashboard.jsx'
import TestModel from './pages/TestModel.jsx'
import DetailedReport from './pages/DetailedReport.jsx'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const rememberMe  = localStorage.getItem('rememberMe') === 'true';
    const sessionFlag = sessionStorage.getItem('loggedIn') === 'true';

    // No storage flag on this device/tab → skip server call entirely.
    // This enforces device-specific auth isolation.
    if (!rememberMe && !sessionFlag) {
      setLoading(false);
      return;
    }

    try {
      const response = await api.get('/api/check-auth');
      if (response.data.authenticated) {
        setIsAuthenticated(true);
        setUser(response.data.user);
      } else {
        // Server session expired — clear stale local flags
        clearAuthFlags();
      }
    } catch (error) {
      if (error.response && error.response.status === 401) {
        // Definitive "not authenticated" response from server
        clearAuthFlags();
      }
      // Network error / server down: keep flags so we retry on next load
      // rather than logging the user out just because of a flaky connection.
    } finally {
      setLoading(false);
    }
  };

  const clearAuthFlags = () => {
    localStorage.removeItem('rememberMe');
    sessionStorage.removeItem('loggedIn');
  };

  const handleLogin = (userData, rememberMe = false) => {
    setIsAuthenticated(true);
    setUser(userData);

    if (rememberMe) {
      localStorage.setItem('rememberMe', 'true');
      sessionStorage.removeItem('loggedIn');
    } else {
      sessionStorage.setItem('loggedIn', 'true');
      localStorage.removeItem('rememberMe');
    }
  };

  const handleLogout = async () => {
    try {
      await api.post('/api/logout');
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setIsAuthenticated(false);
      setUser(null);
      clearAuthFlags();
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loader"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to="/dashboard" />
              ) : (
                <Login onLogin={handleLogin} />
              )
            }
          />
          <Route
            path="/signup"
            element={
              isAuthenticated ? (
                <Navigate to="/dashboard" />
              ) : (
                // Signup uses rememberMe=true: user just created their account,
                // they should stay logged in across browser restarts.
                <Signup onSignup={(userData) => handleLogin(userData, true)} />
              )
            }
          />
          <Route
            path="/dashboard"
            element={
              isAuthenticated ? (
                <Dashboard user={user} onLogout={handleLogout} />
              ) : (
                <Navigate to="/login" />
              )
            }
          />
          <Route
            path="/test-model"
            element={
              isAuthenticated ? (
                <TestModel user={user} onLogout={handleLogout} />
              ) : (
                <Navigate to="/login" />
              )
            }
          />
          <Route
            path="/report/:reportId"
            element={
              isAuthenticated ? (
                <DetailedReport user={user} onLogout={handleLogout} />
              ) : (
                <Navigate to="/login" />
              )
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;