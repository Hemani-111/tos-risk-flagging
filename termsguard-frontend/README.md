# TermsGuard React frontend

Run `npm install` then `npm run dev`. Copy `.env.example` to `.env` and configure the FastAPI origin. Run `npm run build` for a production bundle.

Includes Home, Analyze (file/paste API integration), Results, illustrative Example, Research, and How it works. API response adapter is `normalize` in src/lib/api.js. Adjust it to match your actual response schema. Expected clauses expose text and label (or clause_text/prediction). Backend CORS must permit the Vite origin, usually http://localhost:5173.

This package has not been verified against your latest local backend. Research tables/charts require your canonical comparison data and are explicitly marked as unavailable. Review currently renders segmented clauses; it does not reconstruct the entire extracted document using offsets. Preserve your backend extractedText and offset handling when integrating the full original-text viewer. No model weights or invented research scores are included.

## Pages

Each route has a separate component under `src/pages/`. `src/App.jsx` contains routing and the shared header; `src/lib/api.js` contains the backend calls and response adapter.
