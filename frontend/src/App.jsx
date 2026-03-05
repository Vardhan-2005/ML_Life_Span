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
    // Check both storages for a saved login flag
    const rememberMe = localStorage.getItem('rememberMe') === 'true';
    const sessionFlag = sessionStorage.getItem('loggedIn') === 'true';

    // Only attempt to restore session if a flag exists in either storage
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
        // Server session expired — clear stale flags
        localStorage.removeItem('rememberMe');
        sessionStorage.removeItem('loggedIn');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('rememberMe');
      sessionStorage.removeItem('loggedIn');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (userData, rememberMe = false) => {
    setIsAuthenticated(true);
    setUser(userData);

    if (rememberMe) {
      // Persists across browser restarts on this device
      localStorage.setItem('rememberMe', 'true');
      sessionStorage.removeItem('loggedIn');
    } else {
      // Lives only until the tab/browser is closed
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
      localStorage.removeItem('rememberMe');
      sessionStorage.removeItem('loggedIn');
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
                <Signup onSignup={handleLogin} />
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