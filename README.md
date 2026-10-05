# project name

Understand what you're agreeing to.

---

## Download

```bash
git clone <repository-url>
cd ToS-risk-flagging
```

---

## Start

### Backend

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`

---

## Notes

- No virtual environment required
- The ML model is not yet connected. Document upload works, but clause-level risk analysis is not available until the model is trained.
- This is an educational screening tool and does not provide legal advice.
