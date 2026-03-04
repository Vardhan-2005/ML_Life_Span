from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sys
import psycopg2
import json
import tempfile
from datetime import datetime, timedelta
import secrets

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import init_database, get_connection
from ml_engine.drift_detector import DriftDetector
from ml_engine.lifespan_predictor import LifespanPredictor

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

_ALLOWED_ORIGINS = os.environ.get(
    'ALLOWED_ORIGINS',
    'http://localhost:3000'
).split(',')
CORS(app, supports_credentials=True, origins=_ALLOWED_ORIGINS)

ALLOWED_EXTENSIONS = {'csv'}

init_database()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated


# =====================================================================
# AUTH
# =====================================================================

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not username or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        password_hash = generate_password_hash(password)
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id',
                (username, email, password_hash)
            )
            user_id = cursor.fetchone()[0]
            conn.commit()
            session.permanent = True
            session['user_id'] = user_id
            session['username'] = username
            return jsonify({
                'message': 'Signup successful',
                'user': {'id': user_id, 'username': username, 'email': email}
            }), 201
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return jsonify({'error': 'Username or email already exists'}), 409
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, email, password_hash FROM users WHERE username = %s',
            (username,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user[3], password):
            session.permanent = True
            session['user_id'] = user[0]
            session['username'] = user[1]
            return jsonify({
                'message': 'Login successful',
                'user': {'id': user[0], 'username': user[1], 'email': user[2]}
            }), 200
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200


@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {'id': session['user_id'], 'username': session['username']}
        }), 200
    return jsonify({'authenticated': False}), 200


# =====================================================================
# FILE UPLOAD — stored in DB, NOT on disk
# =====================================================================

def _store_files_in_db(files, file_type: str, user_id: int):
    saved = []
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for file in files:
            if not (file and allowed_file(file.filename)):
                continue
            original_name = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            stored_name = f"{timestamp}_{original_name}"
            content = file.read().decode('utf-8')
            size = len(content.encode('utf-8'))

            cursor.execute(
                '''INSERT INTO uploaded_files
                   (user_id, file_type, original_name, stored_name, file_content, file_size)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id''',
                (user_id, file_type, original_name, stored_name, content, size)
            )
            file_id = cursor.fetchone()[0]
            saved.append({
                'id': file_id,
                'name': original_name,
                'stored_name': stored_name,
            })
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
    return saved


@app.route('/api/upload-baseline', methods=['POST'])
@require_auth
def upload_baseline():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400

        saved = _store_files_in_db(files, 'baseline', session['user_id'])
        if not saved:
            return jsonify({'error': 'No valid CSV files uploaded'}), 400

        return jsonify({
            'message': f'{len(saved)} baseline file(s) uploaded successfully',
            'files': saved
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload-current', methods=['POST'])
@require_auth
def upload_current():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400

        saved = _store_files_in_db(files, 'current', session['user_id'])
        if not saved:
            return jsonify({'error': 'No valid CSV files uploaded'}), 400

        return jsonify({
            'message': f'{len(saved)} current file(s) uploaded successfully',
            'files': saved
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =====================================================================
# DRIFT DETECTION
# =====================================================================

def _load_csv_from_db(file_ids: list, user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    tmp_paths = []
    tmp_dir = tempfile.mkdtemp()

    for fid in file_ids:
        cursor.execute(
            'SELECT file_content, stored_name FROM uploaded_files WHERE id = %s AND user_id = %s',
            (fid, user_id)
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            raise ValueError(f'File {fid} not found or access denied')
        content, stored_name = row
        tmp_path = os.path.join(tmp_dir, stored_name)
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        tmp_paths.append(tmp_path)

    cursor.close()
    conn.close()
    return tmp_paths, tmp_dir


@app.route('/api/run-drift', methods=['POST'])
@require_auth
def run_drift():
    try:
        data = request.get_json()
        report_name = data.get('report_name', f"Drift Report {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        baseline_files = data.get('baseline_files', [])
        current_files  = data.get('current_files', [])

        if not baseline_files or not current_files:
            return jsonify({'error': 'Both baseline and current files are required'}), 400

        baseline_ids = [f['id'] for f in baseline_files]
        current_ids  = [f['id'] for f in current_files]

        baseline_paths, b_tmp = _load_csv_from_db(baseline_ids, session['user_id'])
        current_paths,  c_tmp = _load_csv_from_db(current_ids,  session['user_id'])

        try:
            detector = DriftDetector(n_bins=10)
            drift_results = detector.detect_drift(baseline_paths, current_paths)
        finally:
            import shutil
            shutil.rmtree(b_tmp, ignore_errors=True)
            shutil.rmtree(c_tmp, ignore_errors=True)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO drift_reports
            (user_id, report_name, overall_drift_score, drift_status,
             baseline_files, current_files, total_features, drifted_features)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        ''', (
            session['user_id'],
            report_name,
            drift_results['overall_drift_score'],
            drift_results['overall_status'],
            json.dumps([f['name'] for f in baseline_files]),
            json.dumps([f['name'] for f in current_files]),
            drift_results['total_features'],
            drift_results['drifted_features'],
        ))
        report_id = cursor.fetchone()[0]

        for feature in drift_results['feature_results']:
            cursor.execute('''
                INSERT INTO drift_features
                (report_id, feature_name, psi_score, kl_divergence, js_divergence,
                 ks_statistic, ks_pvalue, drift_status, baseline_mean, current_mean,
                 baseline_std, current_std)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                report_id,
                feature['feature_name'],
                feature['psi_score'],
                feature['kl_divergence'],
                feature['js_divergence'],
                feature['ks_statistic'],
                feature['ks_pvalue'],
                feature['drift_status'],
                feature['baseline_mean'],
                feature['current_mean'],
                feature['baseline_std'],
                feature['current_std'],
            ))

        cursor.execute('''
            SELECT overall_drift_score FROM drift_reports
            WHERE user_id = %s AND id != %s
            ORDER BY created_at DESC LIMIT 10
        ''', (session['user_id'], report_id))
        history_rows = cursor.fetchall()
        historical = [{'overall_drift_score': r[0]} for r in reversed(history_rows)]

        predictor = LifespanPredictor()
        lifespan = predictor.predict_lifespan(drift_results, historical)

        cursor.execute('''
            INSERT INTO lifespan_predictions
            (report_id, health_score, health_label, health_percentage,
             days_remaining, recommended_retrain_date, confidence,
             velocity, velocity_label, trend_direction, trend_json,
             risk_factors_json, feature_insights_json, recommendation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            report_id,
            lifespan['health_score'],
            lifespan['health_label'],
            lifespan['health_percentage'],
            lifespan['days_remaining'],
            lifespan['recommended_retrain_date'],
            lifespan['confidence'],
            lifespan['velocity'],
            lifespan['velocity_label'],
            lifespan['trend'].get('direction'),
            json.dumps(lifespan['trend']),
            json.dumps(lifespan['risk_factors']),
            json.dumps(lifespan['feature_insights']),
            lifespan['recommendation'],
        ))

        conn.commit()
        cursor.close()
        conn.close()

        drift_results['report_id']   = report_id
        drift_results['report_name'] = report_name
        drift_results['lifespan']    = lifespan

        return jsonify({
            'message': 'Drift detection completed successfully',
            'results': drift_results
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/get-history', methods=['GET'])
@require_auth
def get_history():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dr.id, dr.report_name, dr.overall_drift_score, dr.drift_status,
                   dr.total_features, dr.drifted_features, dr.created_at,
                   lp.health_label, lp.days_remaining, lp.health_percentage
            FROM drift_reports dr
            LEFT JOIN lifespan_predictions lp ON lp.report_id = dr.id
            WHERE dr.user_id = %s
            ORDER BY dr.created_at DESC
            LIMIT 50
        ''', (session['user_id'],))

        reports = []
        for row in cursor.fetchall():
            reports.append({
                'id': row[0],
                'report_name': row[1],
                'overall_drift_score': row[2],
                'drift_status': row[3],
                'total_features': row[4],
                'drifted_features': row[5],
                'created_at': row[6].isoformat() if row[6] else None,
                'health_label': row[7],
                'days_remaining': row[8],
                'health_percentage': row[9],
            })
        cursor.close()
        conn.close()
        return jsonify({'reports': reports}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/get-report/<int:report_id>', methods=['GET'])
@require_auth
def get_report(report_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, report_name, overall_drift_score, drift_status,
                   baseline_files, current_files, total_features, drifted_features, created_at
            FROM drift_reports WHERE id = %s AND user_id = %s
        ''', (report_id, session['user_id']))
        report_row = cursor.fetchone()
        if not report_row:
            return jsonify({'error': 'Report not found'}), 404

        report = {
            'id': report_row[0],
            'report_name': report_row[1],
            'overall_drift_score': report_row[2],
            'drift_status': report_row[3],
            'baseline_files': json.loads(report_row[4]),
            'current_files': json.loads(report_row[5]),
            'total_features': report_row[6],
            'drifted_features': report_row[7],
            'created_at': report_row[8].isoformat() if report_row[8] else None,
        }

        cursor.execute('''
            SELECT feature_name, psi_score, kl_divergence, js_divergence,
                   ks_statistic, ks_pvalue, drift_status, baseline_mean,
                   current_mean, baseline_std, current_std
            FROM drift_features WHERE report_id = %s
            ORDER BY
                CASE drift_status WHEN 'Drift' THEN 1 WHEN 'Warning' THEN 2 ELSE 3 END,
                psi_score DESC
        ''', (report_id,))

        report['features'] = [{
            'feature_name': r[0], 'psi_score': r[1], 'kl_divergence': r[2],
            'js_divergence': r[3], 'ks_statistic': r[4], 'ks_pvalue': r[5],
            'drift_status': r[6], 'baseline_mean': r[7], 'current_mean': r[8],
            'baseline_std': r[9], 'current_std': r[10],
        } for r in cursor.fetchall()]

        cursor.execute('''
            SELECT health_score, health_label, health_percentage, days_remaining,
                   recommended_retrain_date, confidence, velocity, velocity_label,
                   trend_direction, trend_json, risk_factors_json,
                   feature_insights_json, recommendation, predicted_at
            FROM lifespan_predictions WHERE report_id = %s
        ''', (report_id,))
        lp_row = cursor.fetchone()
        if lp_row:
            report['lifespan'] = {
                'health_score': lp_row[0],
                'health_label': lp_row[1],
                'health_percentage': lp_row[2],
                'days_remaining': lp_row[3],
                'recommended_retrain_date': lp_row[4],
                'confidence': lp_row[5],
                'velocity': lp_row[6],
                'velocity_label': lp_row[7],
                'trend_direction': lp_row[8],
                'trend': json.loads(lp_row[9]) if lp_row[9] else {},
                'risk_factors': json.loads(lp_row[10]) if lp_row[10] else [],
                'feature_insights': json.loads(lp_row[11]) if lp_row[11] else {},
                'recommendation': lp_row[12],
                'predicted_at': lp_row[13].isoformat() if lp_row[13] else None,
            }

        cursor.close()
        conn.close()
        return jsonify({'report': report}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/get-lifespan/<int:report_id>', methods=['GET'])
@require_auth
def get_lifespan(report_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id FROM drift_reports WHERE id = %s AND user_id = %s',
            (report_id, session['user_id'])
        )
        if not cursor.fetchone():
            return jsonify({'error': 'Report not found'}), 404

        cursor.execute(
            '''SELECT health_score, health_label, health_percentage, days_remaining,
                      recommended_retrain_date, confidence, velocity, velocity_label,
                      trend_direction, trend_json, risk_factors_json,
                      feature_insights_json, recommendation, predicted_at
               FROM lifespan_predictions WHERE report_id = %s''',
            (report_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return jsonify({'error': 'No lifespan prediction for this report'}), 404

        return jsonify({'lifespan': {
            'health_score': row[0],
            'health_label': row[1],
            'health_percentage': row[2],
            'days_remaining': row[3],
            'recommended_retrain_date': row[4],
            'confidence': row[5],
            'velocity': row[6],
            'velocity_label': row[7],
            'trend_direction': row[8],
            'trend': json.loads(row[9]) if row[9] else {},
            'risk_factors': json.loads(row[10]) if row[10] else [],
            'feature_insights': json.loads(row[11]) if row[11] else {},
            'recommendation': row[12],
            'predicted_at': row[13].isoformat() if row[13] else None,
        }}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
