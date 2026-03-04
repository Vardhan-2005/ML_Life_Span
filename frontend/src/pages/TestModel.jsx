import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Navbar from '../components/Navbar';
import '../styles/TestModel.css';

function TestModel({ user, onLogout }) {
  const [reportName, setReportName] = useState('');
  const [baselineFiles, setBaselineFiles] = useState([]);
  const [currentFiles, setCurrentFiles] = useState([]);
  const [uploadedBaseline, setUploadedBaseline] = useState([]);
  const [uploadedCurrent, setUploadedCurrent] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1);
  const navigate = useNavigate();

  const handleBaselineChange = (e) => {
    const files = Array.from(e.target.files);
    setBaselineFiles(files);
  };

  const handleCurrentChange = (e) => {
    const files = Array.from(e.target.files);
    setCurrentFiles(files);
  };

  const uploadBaseline = async () => {
    if (baselineFiles.length === 0) {
      setError('Please select baseline files');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      baselineFiles.forEach(file => {
        formData.append('files', file);
      });

      const response = await axios.post('/api/upload-baseline', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setUploadedBaseline(response.data.files);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload baseline files');
    } finally {
      setLoading(false);
    }
  };

  const uploadCurrent = async () => {
    if (currentFiles.length === 0) {
      setError('Please select current files');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      currentFiles.forEach(file => {
        formData.append('files', file);
      });

      const response = await axios.post('/api/upload-current', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setUploadedCurrent(response.data.files);
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload current files');
    } finally {
      setLoading(false);
    }
  };

  const runDriftDetection = async () => {
    if (!reportName.trim()) {
      setError('Please enter a report name');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/run-drift', {
        report_name: reportName,
        baseline_files: uploadedBaseline,
        current_files: uploadedCurrent
      });

      const reportId = response.data.results.report_id;
      navigate(`/report/${reportId}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to run drift detection');
    } finally {
      setLoading(false);
    }
  };

  const resetProcess = () => {
    setStep(1);
    setBaselineFiles([]);
    setCurrentFiles([]);
    setUploadedBaseline([]);
    setUploadedCurrent([]);
    setReportName('');
    setError('');
  };

  return (
    <div className="page-container">
      <Navbar user={user} onLogout={onLogout} />
      
      <div className="content-wrapper">
        <div className="page-header">
          <div>
            <h1>Run Drift Detection</h1>
            <p className="subtitle">Upload your datasets and detect distribution changes</p>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="steps-container">
          <div className={`step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
            <div className="step-number">{step > 1 ? '✓' : '1'}</div>
            <div className="step-label">Upload Baseline</div>
          </div>
          <div className={`step-line ${step > 1 ? 'completed' : ''}`}></div>
          <div className={`step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
            <div className="step-number">{step > 2 ? '✓' : '2'}</div>
            <div className="step-label">Upload Current</div>
          </div>
          <div className={`step-line ${step > 2 ? 'completed' : ''}`}></div>
          <div className={`step ${step >= 3 ? 'active' : ''}`}>
            <div className="step-number">3</div>
            <div className="step-label">Run Detection</div>
          </div>
        </div>

        {error && (
          <div className="alert alert-error">
            <span className="alert-icon">⚠</span>
            {error}
          </div>
        )}

        {/* Step 1: Baseline Upload */}
        {step === 1 && (
          <div className="card upload-card">
            <div className="card-header">
              <h2>Step 1: Upload Baseline Data</h2>
              <p>Upload one or more CSV files containing your baseline/reference data</p>
            </div>

            <div className="upload-area">
              <input
                type="file"
                id="baseline-upload"
                multiple
                accept=".csv"
                onChange={handleBaselineChange}
                className="file-input"
              />
              <label htmlFor="baseline-upload" className="upload-label">
                <div className="upload-icon">📁</div>
                <div className="upload-text">
                  <strong>Click to upload</strong> or drag and drop
                </div>
                <div className="upload-hint">CSV files only (Multiple files supported)</div>
              </label>
            </div>

            {baselineFiles.length > 0 && (
              <div className="file-list">
                <h3>Selected Files ({baselineFiles.length})</h3>
                {baselineFiles.map((file, index) => (
                  <div key={index} className="file-item">
                    <span className="file-icon">📄</span>
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">{(file.size / 1024).toFixed(2)} KB</span>
                  </div>
                ))}
              </div>
            )}

            <div className="card-actions">
              <button
                className="primary-button"
                onClick={uploadBaseline}
                disabled={loading || baselineFiles.length === 0}
              >
                {loading ? (
                  <>
                    <span className="button-loader"></span>
                    Uploading...
                  </>
                ) : (
                  'Upload & Continue'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Current Upload */}
        {step === 2 && (
          <div className="card upload-card">
            <div className="card-header">
              <h2>Step 2: Upload Current Data</h2>
              <p>Upload one or more CSV files containing your current/production data</p>
            </div>

            <div className="upload-area">
              <input
                type="file"
                id="current-upload"
                multiple
                accept=".csv"
                onChange={handleCurrentChange}
                className="file-input"
              />
              <label htmlFor="current-upload" className="upload-label">
                <div className="upload-icon">📁</div>
                <div className="upload-text">
                  <strong>Click to upload</strong> or drag and drop
                </div>
                <div className="upload-hint">CSV files only (Multiple files supported)</div>
              </label>
            </div>

            {currentFiles.length > 0 && (
              <div className="file-list">
                <h3>Selected Files ({currentFiles.length})</h3>
                {currentFiles.map((file, index) => (
                  <div key={index} className="file-item">
                    <span className="file-icon">📄</span>
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">{(file.size / 1024).toFixed(2)} KB</span>
                  </div>
                ))}
              </div>
            )}

            <div className="card-actions">
              <button className="secondary-button" onClick={() => setStep(1)}>
                Back
              </button>
              <button
                className="primary-button"
                onClick={uploadCurrent}
                disabled={loading || currentFiles.length === 0}
              >
                {loading ? (
                  <>
                    <span className="button-loader"></span>
                    Uploading...
                  </>
                ) : (
                  'Upload & Continue'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Run Detection */}
        {step === 3 && (
          <div className="card upload-card">
            <div className="card-header">
              <h2>Step 3: Run Drift Detection</h2>
              <p>Review your files and start the drift analysis</p>
            </div>

            <div className="summary-section">
              <div className="summary-item">
                <h3>Baseline Files</h3>
                <div className="summary-files">
                  {uploadedBaseline.map((file, index) => (
                    <div key={index} className="summary-file">
                      <span className="file-icon">📄</span>
                      {file.name}
                    </div>
                  ))}
                </div>
              </div>

              <div className="summary-item">
                <h3>Current Files</h3>
                <div className="summary-files">
                  {uploadedCurrent.map((file, index) => (
                    <div key={index} className="summary-file">
                      <span className="file-icon">📄</span>
                      {file.name}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="report-name">Report Name</label>
              <input
                type="text"
                id="report-name"
                value={reportName}
                onChange={(e) => setReportName(e.target.value)}
                placeholder="Enter a name for this drift report"
                className="form-input"
              />
            </div>

            <div className="card-actions">
              <button className="secondary-button" onClick={resetProcess}>
                Start Over
              </button>
              <button
                className="primary-button"
                onClick={runDriftDetection}
                disabled={loading || !reportName.trim()}
              >
                {loading ? (
                  <>
                    <span className="button-loader"></span>
                    Analyzing...
                  </>
                ) : (
                  '🚀 Run Drift Detection'
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default TestModel;
