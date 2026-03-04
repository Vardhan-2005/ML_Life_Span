# ML Data Drift Detection Platform

A complete, production-ready web application for detecting and analyzing data drift in machine learning datasets using multiple statistical metrics.

## 🎯 Features

### Core Functionality
- **User Authentication**: Secure signup, login, and session management
- **Multi-File CSV Upload**: Upload and merge multiple baseline and current datasets
- **Advanced Drift Detection**: 
  - Population Stability Index (PSI)
  - Kullback-Leibler Divergence
  - Jensen-Shannon Divergence
  - Kolmogorov-Smirnov Test
- **Interactive Dashboard**: View drift history and statistics
- **Detailed Reports**: Feature-level analysis with visualizations
- **Persistent Storage**: SQLite database for user data and reports

### Technical Highlights
- **Frontend**: React 18 with modern CSS animations and responsive design
- **Backend**: Flask REST API with proper authentication
- **ML Engine**: Custom drift detection algorithms (no placeholders)
- **Database**: SQLite with normalized schema
- **Charts**: Interactive visualizations using Chart.js

## 📁 Project Structure

```
ml-drift-platform/
├── backend/
│   ├── app.py                 # Flask API server
│   └── uploads/               # User-uploaded files
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   └── Navbar.js
│   │   ├── pages/
│   │   │   ├── Login.js
│   │   │   ├── Signup.js
│   │   │   ├── Dashboard.js
│   │   │   ├── TestModel.js
│   │   │   └── DetailedReport.js
│   │   ├── styles/
│   │   │   ├── App.css
│   │   │   ├── Auth.css
│   │   │   ├── Dashboard.css
│   │   │   ├── TestModel.css
│   │   │   ├── DetailedReport.css
│   │   │   └── Navbar.css
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
├── ml_engine/
│   ├── __init__.py
│   └── drift_detector.py     # Complete drift detection logic
├── database/
│   ├── schema.py              # Database initialization
│   └── drift_platform.db      # SQLite database (created on first run)
├── requirements.txt
├── sample_data_baseline.csv   # Sample baseline data
├── sample_data_current.csv    # Sample current data with drift
└── README.md
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn

### Step 1: Clone/Download Project
```bash
cd ml-drift-platform
```

### Step 2: Backend Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize database:
```bash
cd database
python schema.py
cd ..
```

3. Start Flask server:
```bash
cd backend
python app.py
```

The backend will run on `http://localhost:5000`

### Step 3: Frontend Setup

1. Install Node dependencies:
```bash
cd frontend
npm install
```

2. Start React development server:
```bash
npm start
```

The frontend will run on `http://localhost:3000`

## 📖 Usage Guide

### 1. Create an Account
- Navigate to `http://localhost:3000`
- Click "Sign up" and create your account
- Login with your credentials

### 2. Run Drift Detection

#### Step 1: Upload Baseline Data
- Click "Test Model" or "+ New Drift Test"
- Upload one or more CSV files containing your baseline/reference data
- Click "Upload & Continue"

#### Step 2: Upload Current Data
- Upload one or more CSV files containing your current/production data
- Click "Upload & Continue"

#### Step 3: Run Analysis
- Enter a name for your report
- Click "Run Drift Detection"
- Wait for analysis to complete

### 3. View Results
- See overall drift score and status
- View feature-level analysis with all metrics
- Explore interactive charts
- Check interpretation guide for understanding metrics

### 4. Access History
- Return to Dashboard to view all past reports
- Click "View Details" on any report to see full analysis

## 🧪 Testing with Sample Data

Sample CSV files are included for quick testing:

1. **Baseline Data**: `sample_data_baseline.csv`
   - 20 samples with 5 features
   - Original distribution

2. **Current Data**: `sample_data_current.csv`
   - 20 samples with 5 features
   - Intentionally drifted distribution

Upload these files to see the drift detection in action!

## 📊 Understanding Drift Metrics

### PSI (Population Stability Index)
- **< 0.1**: No significant drift
- **0.1 - 0.25**: Moderate drift, investigate
- **> 0.25**: Significant drift, action required

### KL Divergence
- **< 0.1**: Distributions are similar
- **0.1 - 0.5**: Moderate difference
- **> 0.5**: Significant difference

### JS Divergence
- **< 0.1**: Very similar distributions
- **0.1 - 0.3**: Moderate drift
- **> 0.3**: High drift detected

### KS Test
- **p-value > 0.05**: No significant difference
- **p-value < 0.05**: Statistical difference detected
- **p-value < 0.01**: Strong evidence of drift

## 🔧 API Endpoints

### Authentication
- `POST /api/signup` - Create new user account
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/check-auth` - Check authentication status

### File Upload
- `POST /api/upload-baseline` - Upload baseline CSV files
- `POST /api/upload-current` - Upload current CSV files

### Drift Detection
- `POST /api/run-drift` - Run drift detection analysis
- `GET /api/get-history` - Get user's drift report history
- `GET /api/get-report/<id>` - Get detailed report by ID

### Health Check
- `GET /api/health` - API health check

## 🎨 Design Features

### Modern UI/UX
- Gradient backgrounds with animated orbs
- Card-based layout with shadows
- Smooth animations and transitions
- Responsive design for all devices
- Dark theme optimized for readability

### Interactive Elements
- Progress steps for upload workflow
- Loading states with spinners
- Error messages with animations
- Hover effects on buttons and cards
- Real-time form validation

## 🔒 Security Features

- Password hashing using Werkzeug
- Session-based authentication
- CSRF protection
- Secure file uploads with validation
- User data isolation

## 🐛 Troubleshooting

### Backend Issues

**Database not found:**
```bash
cd database
python schema.py
```

**Port already in use:**
```bash
# Change port in backend/app.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Frontend Issues

**CORS errors:**
- Ensure backend is running on port 5000
- Check CORS configuration in backend/app.py

**Dependencies not installed:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Common Issues

**CSV upload fails:**
- Ensure CSV files have numeric columns
- Check file size (max 50MB)
- Verify CSV format is valid

**Drift detection errors:**
- Ensure baseline and current files have common numeric features
- Check that files have sufficient data (minimum 10 rows recommended)

## 📝 Development Notes

### Database Schema
- **users**: User accounts and authentication
- **drift_reports**: Summary of drift analyses
- **drift_features**: Detailed feature-level metrics

### File Upload Structure
```
backend/uploads/
└── <user_id>/
    ├── baseline/
    │   └── timestamp_filename.csv
    └── current/
        └── timestamp_filename.csv
```

### Session Management
- Sessions stored server-side
- 7-day session lifetime
- Automatic cleanup on logout

## 🚀 Production Deployment

### Backend
1. Set `app.config['SESSION_COOKIE_SECURE'] = True`
2. Use a production WSGI server (gunicorn)
3. Set up proper CORS origins
4. Use environment variables for secrets

### Frontend
1. Build production version: `npm run build`
2. Serve static files with nginx or similar
3. Update API endpoint to production URL

### Database
- Consider migrating to PostgreSQL for production
- Set up regular backups
- Implement connection pooling

## 📄 License

This project is a demonstration application for educational purposes.

## 👥 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the usage guide
3. Examine sample data for reference

## 🎉 Credits

Built with:
- React 18
- Flask 3.0
- Chart.js 4.4
- Pandas, NumPy, SciPy
- SQLite

---

**Built by**: Senior Full-Stack + ML Engineer
**Version**: 1.0.0
**Status**: Production Ready ✅
