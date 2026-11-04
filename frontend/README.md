# TermsGuard frontend

React single-page application built with Vite. The interface is served at port
3000 in development and in the provided Docker Compose setup.

## Local development

```powershell
npm ci
npm run dev
```

Set `VITE_API_URL` in `.env.local` to the FastAPI base URL if it is not
`http://localhost:8000`. The app uses the backend endpoints
`POST /api/v1/documents/analyze` and `POST /api/v1/documents/analyze-text`.

## Build

```powershell
npm run build
npm run preview
```

Analysis results are held in the current browser tab's `sessionStorage` so the
reader can be refreshed without uploading again. Uploaded document content is
sent to the configured API for analysis; it is not written to browser storage.
