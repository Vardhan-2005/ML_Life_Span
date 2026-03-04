import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from "../api/api"
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import Navbar from '../components/Navbar';
import '../styles/DetailedReport.css';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

function DetailedReport({ user, onLogout }) {
  const { reportId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchReport();
  }, [reportId]);

  const fetchReport = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/get-report/${reportId}`);
      setReport(response.data.report);
    } catch (err) {
      setError('Failed to load report');
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

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="page-container">
        <Navbar user={user} onLogout={onLogout} />
        <div className="content-wrapper">
          <div className="loading-state">
            <div className="loader"></div>
            <p>Loading report...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="page-container">
        <Navbar user={user} onLogout={onLogout} />
        <div className="content-wrapper">
          <div className="error-state">
            <p>{error || 'Report not found'}</p>
            <Link to="/dashboard" className="primary-button">Back to Dashboard</Link>
          </div>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const statusCounts = {
    OK: report.features.filter(f => f.drift_status === 'OK').length,
    Warning: report.features.filter(f => f.drift_status === 'Warning').length,
    Drift: report.features.filter(f => f.drift_status === 'Drift').length
  };

  const pieData = {
    labels: ['No Drift', 'Warning', 'Drift Detected'],
    datasets: [{
      data: [statusCounts.OK, statusCounts.Warning, statusCounts.Drift],
      backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
      borderWidth: 0
    }]
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 15,
          font: { size: 12 }
        }
      }
    }
  };

  // Top drifted features for bar chart
  const topDrifted = [...report.features]
    .filter(f => f.psi_score !== null)
    .sort((a, b) => b.psi_score - a.psi_score)
    .slice(0, 10);

  const barData = {
    labels: topDrifted.map(f => f.feature_name),
    datasets: [{
      label: 'PSI Score',
      data: topDrifted.map(f => f.psi_score),
      backgroundColor: topDrifted.map(f => {
        if (f.drift_status === 'Drift') return '#ef4444';
        if (f.drift_status === 'Warning') return '#f59e0b';
        return '#10b981';
      })
    }]
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: 'Top 10 Features by PSI Score',
        font: { size: 14 }
      }
    },
    scales: {
      x: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'PSI Score'
        }
      }
    }
  };

  return (
    <div className="page-container">
      <Navbar user={user} onLogout={onLogout} />
      
      <div className="content-wrapper">
        <div className="page-header">
          <div>
            <Link to="/dashboard" className="breadcrumb">← Back to Dashboard</Link>
            <h1>{report.report_name}</h1>
            <p className="subtitle">Created on {formatDate(report.created_at)}</p>
          </div>
          <span
            className="status-badge-large"
            style={{ backgroundColor: getStatusColor(report.drift_status) }}
          >
            {report.drift_status}
          </span>
        </div>

        {/* Summary Cards */}
        <div className="summary-grid">
          <div className="summary-card">
            <div className="summary-icon" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              📊
            </div>
            <div className="summary-content">
              <div className="summary-value">{(report.overall_drift_score * 100).toFixed(1)}%</div>
              <div className="summary-label">Overall Drift Score</div>
            </div>
          </div>

          <div className="summary-card">
            <div className="summary-icon" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              🎯
            </div>
            <div className="summary-content">
              <div className="summary-value">{report.total_features}</div>
              <div className="summary-label">Total Features</div>
            </div>
          </div>

          <div className="summary-card">
            <div className="summary-icon" style={{ background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' }}>
              ⚠
            </div>
            <div className="summary-content">
              <div className="summary-value">{report.drifted_features}</div>
              <div className="summary-label">Drifted Features</div>
            </div>
          </div>

          <div className="summary-card">
            <div className="summary-icon" style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}>
              ✓
            </div>
            <div className="summary-content">
              <div className="summary-value">{statusCounts.OK}</div>
              <div className="summary-label">Stable Features</div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="charts-grid">
          <div className="card chart-card">
            <div className="card-header">
              <h2>Drift Status Distribution</h2>
            </div>
            <div className="chart-container-pie">
              <Pie data={pieData} options={pieOptions} />
            </div>
          </div>

          <div className="card chart-card">
            <div className="card-header">
              <h2>Top Features by Drift Score</h2>
            </div>
            <div className="chart-container-bar">
              <Bar data={barData} options={barOptions} />
            </div>
          </div>
        </div>

        {/* Files Used */}
        <div className="card">
          <div className="card-header">
            <h2>Dataset Information</h2>
          </div>
          <div className="files-grid">
            <div className="files-section">
              <h3>Baseline Files</h3>
              <div className="file-badges">
                {report.baseline_files.map((file, index) => (
                  <span key={index} className="file-badge">📄 {file}</span>
                ))}
              </div>
            </div>
            <div className="files-section">
              <h3>Current Files</h3>
              <div className="file-badges">
                {report.current_files.map((file, index) => (
                  <span key={index} className="file-badge">📄 {file}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Feature Table */}
        <div className="card">
          <div className="card-header">
            <h2>Feature-Level Analysis</h2>
            <span className="badge">{report.features.length} features</span>
          </div>

          <div className="table-container">
            <table className="feature-table">
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>Status</th>
                  <th>PSI</th>
                  <th>KL Div</th>
                  <th>JS Div</th>
                  <th>KS Test</th>
                  <th>Baseline Mean</th>
                  <th>Current Mean</th>
                  <th>Mean Change</th>
                </tr>
              </thead>
              <tbody>
                {report.features.map((feature, index) => {
                  const meanChange = feature.baseline_mean !== 0
                    ? ((feature.current_mean - feature.baseline_mean) / feature.baseline_mean * 100)
                    : 0;

                  return (
                    <tr key={index} className={`row-${feature.drift_status.toLowerCase()}`}>
                      <td>
                        <strong>{feature.feature_name}</strong>
                      </td>
                      <td>
                        <span
                          className="status-badge-small"
                          style={{ backgroundColor: getStatusColor(feature.drift_status) }}
                        >
                          {feature.drift_status}
                        </span>
                      </td>
                      <td>{feature.psi_score !== null ? feature.psi_score.toFixed(4) : 'N/A'}</td>
                      <td>{feature.kl_divergence !== null ? feature.kl_divergence.toFixed(4) : 'N/A'}</td>
                      <td>{feature.js_divergence !== null ? feature.js_divergence.toFixed(4) : 'N/A'}</td>
                      <td>
                        {feature.ks_statistic !== null ? (
                          <>
                            <div>{feature.ks_statistic.toFixed(4)}</div>
                            <small className="p-value">p={feature.ks_pvalue.toFixed(4)}</small>
                          </>
                        ) : 'N/A'}
                      </td>
                      <td>{feature.baseline_mean.toFixed(4)}</td>
                      <td>{feature.current_mean.toFixed(4)}</td>
                      <td>
                        <span className={meanChange > 0 ? 'change-positive' : 'change-negative'}>
                          {meanChange > 0 ? '+' : ''}{meanChange.toFixed(2)}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── ML Lifespan Prediction Panel ─────────────────────────────── */}
        {report.lifespan && (
          <div className="card" style={{ borderLeft: `4px solid ${
            report.lifespan.health_label === 'Excellent' ? '#10b981' :
            report.lifespan.health_label === 'Good'      ? '#3b82f6' :
            report.lifespan.health_label === 'Fair'      ? '#f59e0b' :
            report.lifespan.health_label === 'Poor'      ? '#f97316' : '#ef4444'
          }` }}>
            <div className="card-header" style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <h2>🤖 ML Lifespan Prediction</h2>
              <span style={{
                background: report.lifespan.health_label === 'Excellent' ? '#10b981' :
                            report.lifespan.health_label === 'Good'      ? '#3b82f6' :
                            report.lifespan.health_label === 'Fair'      ? '#f59e0b' :
                            report.lifespan.health_label === 'Poor'      ? '#f97316' : '#ef4444',
                color:'#fff', padding:'4px 14px', borderRadius:'9999px', fontWeight:700, fontSize:'0.9rem'
              }}>
                {report.lifespan.health_label}
              </span>
            </div>

            {/* Top metrics row */}
            <div className="summary-grid" style={{ marginBottom:'1.5rem' }}>
              <div className="summary-card">
                <div className="summary-icon" style={{ background:'linear-gradient(135deg,#3b82f6,#6366f1)' }}>🩺</div>
                <div className="summary-content">
                  <div className="summary-value">{report.lifespan.health_percentage}%</div>
                  <div className="summary-label">Model Health</div>
                </div>
              </div>
              <div className="summary-card">
                <div className="summary-icon" style={{ background:'linear-gradient(135deg,#f59e0b,#ef4444)' }}>⏳</div>
                <div className="summary-content">
                  <div className="summary-value">{report.lifespan.days_remaining}d</div>
                  <div className="summary-label">Days Remaining</div>
                </div>
              </div>
              <div className="summary-card">
                <div className="summary-icon" style={{ background:'linear-gradient(135deg,#10b981,#059669)' }}>📅</div>
                <div className="summary-content">
                  <div className="summary-value" style={{ fontSize:'1rem' }}>{report.lifespan.recommended_retrain_date}</div>
                  <div className="summary-label">Retrain By</div>
                </div>
              </div>
              <div className="summary-card">
                <div className="summary-icon" style={{ background:'linear-gradient(135deg,#8b5cf6,#6366f1)' }}>📈</div>
                <div className="summary-content">
                  <div className="summary-value">{report.lifespan.velocity_label}</div>
                  <div className="summary-label">Drift Trend</div>
                </div>
              </div>
            </div>

            {/* Health bar */}
            <div style={{ marginBottom:'1.5rem' }}>
              <div style={{ display:'flex', justifyContent:'space-between', marginBottom:6, fontSize:'0.85rem', color:'#6b7280' }}>
                <span>Model Health Score</span>
                <span><strong>{report.lifespan.health_percentage}%</strong> healthy &nbsp;·&nbsp; confidence {Math.round(report.lifespan.confidence * 100)}%</span>
              </div>
              <div style={{ background:'#e5e7eb', borderRadius:8, height:14, overflow:'hidden' }}>
                <div style={{
                  width: `${report.lifespan.health_percentage}%`,
                  height:'100%',
                  background: report.lifespan.health_label === 'Excellent' ? '#10b981' :
                               report.lifespan.health_label === 'Good'      ? '#3b82f6' :
                               report.lifespan.health_label === 'Fair'      ? '#f59e0b' :
                               report.lifespan.health_label === 'Poor'      ? '#f97316' : '#ef4444',
                  transition:'width 0.6s ease',
                  borderRadius:8,
                }} />
              </div>
            </div>

            {/* Recommendation */}
            <div style={{ background:'#f8fafc', border:'1px solid #e2e8f0', borderRadius:8, padding:'1rem', marginBottom:'1.5rem' }}>
              <strong style={{ display:'block', marginBottom:4, color:'#1e293b' }}>💡 Recommendation</strong>
              <p style={{ margin:0, color:'#475569', lineHeight:1.6 }}>{report.lifespan.recommendation}</p>
            </div>

            {/* Risk factors */}
            {report.lifespan.risk_factors && report.lifespan.risk_factors.length > 0 && (
              <div style={{ marginBottom:'1.5rem' }}>
                <strong style={{ display:'block', marginBottom:8, color:'#1e293b' }}>⚠️ Risk Factors</strong>
                <ul style={{ margin:0, paddingLeft:'1.25rem', color:'#64748b', lineHeight:1.8 }}>
                  {report.lifespan.risk_factors.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}

            {/* Top drifted features */}
            {report.lifespan.feature_insights && report.lifespan.feature_insights.top_drifted_features && report.lifespan.feature_insights.top_drifted_features.length > 0 && (
              <div>
                <strong style={{ display:'block', marginBottom:8, color:'#1e293b' }}>🔍 Top Drift-Driving Features</strong>
                <div style={{ display:'flex', flexWrap:'wrap', gap:8 }}>
                  {report.lifespan.feature_insights.top_drifted_features.map((f, i) => (
                    <div key={i} style={{ background:'#fef2f2', border:'1px solid #fecaca', borderRadius:8, padding:'6px 12px', fontSize:'0.85rem' }}>
                      <strong style={{ color:'#dc2626' }}>{f.name}</strong>
                      <span style={{ color:'#6b7280' }}> · PSI {f.psi_score} · Δmean {f.mean_shift_pct}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Interpretation Guide */}
        <div className="card">
          <div className="card-header">
            <h2>Metric Interpretation Guide</h2>
          </div>
          <div className="interpretation-grid">
            <div className="interpretation-item">
              <h3>PSI (Population Stability Index)</h3>
              <p><strong>&lt; 0.1:</strong> No significant drift</p>
              <p><strong>0.1 - 0.25:</strong> Moderate drift, investigate</p>
              <p><strong>&gt; 0.25:</strong> Significant drift, action required</p>
            </div>
            <div className="interpretation-item">
              <h3>KL Divergence</h3>
              <p><strong>&lt; 0.1:</strong> Distributions are similar</p>
              <p><strong>0.1 - 0.5:</strong> Moderate difference</p>
              <p><strong>&gt; 0.5:</strong> Significant difference</p>
            </div>
            <div className="interpretation-item">
              <h3>JS Divergence</h3>
              <p><strong>&lt; 0.1:</strong> Very similar distributions</p>
              <p><strong>0.1 - 0.3:</strong> Moderate drift</p>
              <p><strong>&gt; 0.3:</strong> High drift detected</p>
            </div>
            <div className="interpretation-item">
              <h3>KS Test</h3>
              <p><strong>p-value &gt; 0.05:</strong> No significant difference</p>
              <p><strong>p-value &lt; 0.05:</strong> Statistical difference detected</p>
              <p><strong>p-value &lt; 0.01:</strong> Strong evidence of drift</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DetailedReport;