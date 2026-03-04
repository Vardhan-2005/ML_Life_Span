import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from "../api/api"
import Navbar from '../components/Navbar';
import '../styles/Dashboard.css';

function Dashboard({ user, onLogout }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/get-history');
      setReports(response.data.reports);
    } catch (err) {
      setError('Failed to load reports');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'OK':
        return '#10b981';
      case 'Warning':
        return '#f59e0b';
      case 'Drift':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'OK':
        return '✓';
      case 'Warning':
        return '⚠';
      case 'Drift':
        return '✕';
      default:
        return '•';
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateStats = () => {
    const totalReports = reports.length;
    const driftReports = reports.filter(r => r.drift_status === 'Drift').length;
    const warningReports = reports.filter(r => r.drift_status === 'Warning').length;
    const okReports = reports.filter(r => r.drift_status === 'OK').length;
    
    return { totalReports, driftReports, warningReports, okReports };
  };

  const stats = calculateStats();

  return (
    <div className="page-container">
      <Navbar user={user} onLogout={onLogout} />
      
      <div className="content-wrapper">
        <div className="page-header">
          <div>
            <h1>Dashboard</h1>
            <p className="subtitle">Monitor and analyze your data drift reports</p>
          </div>
          <Link to="/test-model" className="primary-button">
            + New Drift Test
          </Link>
        </div>

        {/* Statistics Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              📊
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.totalReports}</div>
              <div className="stat-label">Total Reports</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}>
              ✓
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.okReports}</div>
              <div className="stat-label">No Drift</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}>
              ⚠
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.warningReports}</div>
              <div className="stat-label">Warning</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' }}>
              ✕
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.driftReports}</div>
              <div className="stat-label">Drift Detected</div>
            </div>
          </div>
        </div>

        {/* Reports History */}
        <div className="card">
          <div className="card-header">
            <h2>Recent Reports</h2>
            <span className="badge">{reports.length} reports</span>
          </div>

          {loading ? (
            <div className="loading-state">
              <div className="loader"></div>
              <p>Loading reports...</p>
            </div>
          ) : error ? (
            <div className="error-state">
              <p>{error}</p>
            </div>
          ) : reports.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <h3>No reports yet</h3>
              <p>Run your first drift detection to see results here</p>
              <Link to="/test-model" className="primary-button">
                Start Drift Test
              </Link>
            </div>
          ) : (
            <div className="reports-table-container">
              <table className="reports-table">
                <thead>
                  <tr>
                    <th>Report Name</th>
                    <th>Status</th>
                    <th>Drift Score</th>
                    <th>Features</th>
                    <th>Drifted</th>
                    <th>Created</th>
                    <th>Health</th>
                    <th>Days Left</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((report) => (
                    <tr key={report.id}>
                      <td>
                        <div className="report-name">
                          <span className="report-icon">📊</span>
                          {report.report_name}
                        </div>
                      </td>
                      <td>
                        <span
                          className="status-badge"
                          style={{ backgroundColor: getStatusColor(report.drift_status) + '20', color: getStatusColor(report.drift_status) }}
                        >
                          {getStatusIcon(report.drift_status)} {report.drift_status}
                        </span>
                      </td>
                      <td>
                        <div className="drift-score">
                          <div className="score-bar">
                            <div
                              className="score-fill"
                              style={{
                                width: `${Math.min(report.overall_drift_score * 100, 100)}%`,
                                backgroundColor: getStatusColor(report.drift_status)
                              }}
                            ></div>
                          </div>
                          <span className="score-value">
                            {(report.overall_drift_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      <td>{report.total_features}</td>
                      <td>
                        <span className={`feature-count ${report.drifted_features > 0 ? 'has-drift' : ''}`}>
                          {report.drifted_features}
                        </span>
                      </td>
                      <td className="date-cell">{formatDate(report.created_at)}</td>
                      <td>
                        {report.health_label ? (
                          <span style={{
                            background:
                              report.health_label === 'Excellent' ? '#d1fae5' :
                              report.health_label === 'Good'      ? '#dbeafe' :
                              report.health_label === 'Fair'      ? '#fef3c7' :
                              report.health_label === 'Poor'      ? '#ffedd5' : '#fee2e2',
                            color:
                              report.health_label === 'Excellent' ? '#065f46' :
                              report.health_label === 'Good'      ? '#1e40af' :
                              report.health_label === 'Fair'      ? '#92400e' :
                              report.health_label === 'Poor'      ? '#9a3412' : '#991b1b',
                            padding: '2px 10px', borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 600
                          }}>
                            {report.health_label}
                          </span>
                        ) : null}
                      </td>
                      <td>
                        {report.days_remaining != null ? (
                          <span style={{ fontWeight: 600, color: report.days_remaining < 14 ? '#ef4444' : report.days_remaining < 45 ? '#f59e0b' : '#10b981' }}>
                            {report.days_remaining}d
                          </span>
                        ) : null}
                      </td>
                      <td>
                        <Link to={`/report/${report.id}`} className="view-button">
                          View Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;