# Deploying LifeSpan to Render

## Prerequisites
- A [Render](https://render.com) account
- Your project pushed to a GitHub/GitLab repo

---

## One-Click Deploy via render.yaml

The `render.yaml` at the repo root configures everything automatically:
- **PostgreSQL** managed database (`lifespan-db`) — free tier
- **Backend** Flask web service (`drift-backend`)
- **Frontend** Vite static site (`drift-frontend`)

### Steps

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New → Blueprint**
2. Connect your GitHub repo
3. Render will detect `render.yaml` and create all services
4. Wait for the database and backend to finish deploying (~3–5 min)
5. After deploy, update these two env vars:
   - `drift-backend` → `ALLOWED_ORIGINS` = `https://drift-frontend.onrender.com`
   - `drift-frontend` → `VITE_API_URL` = `https://drift-backend.onrender.com`
6. Trigger a **Manual Deploy** on both services after updating env vars

---

## Environment Variables Reference

### Backend (`drift-backend`)
| Variable | Value |
|---|---|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | auto-generated |
| `DATABASE_URL` | auto-set from linked PostgreSQL DB |
| `ALLOWED_ORIGINS` | `https://drift-frontend.onrender.com` |

### Frontend (`drift-frontend`)
| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://drift-backend.onrender.com` |

---

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql://user:pass@localhost:5432/lifespan
export SECRET_KEY=dev-secret
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev   # runs on http://localhost:3000
```
The Vite dev server proxies `/api/*` to `http://localhost:5000` automatically.

---

## Notes
- PostgreSQL replaces SQLite — no persistent disk needed on Render
- The free PostgreSQL instance on Render expires after 90 days; upgrade to paid to keep data
- Vite's `dist/` folder is the static build output (previously `build/` with CRA)
