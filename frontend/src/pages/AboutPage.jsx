import { Link } from 'react-router-dom';
import { PRODUCTION_MODEL } from '../lib/comparisonData';

export default function About(){return <section className="panel information-panel">
  <small>HOW IT WORKS</small>
  <h1>Read the wording.<br/>Use labels as a starting point.</h1>
  <p>TermsGuard extracts a document’s text, splits it into clauses, and assigns a model prediction to each clause. Review those predictions alongside the surrounding wording.</p>
  <h2>What the labels mean</h2>
  <p><b>Risky</b> means the clause was predicted to resemble adverse examples in the training data. <b>Neutral</b> means it was predicted to resemble neutral examples. <b>Safe</b> means it was predicted to resemble protective examples. “Safe” is a classification label, not a guarantee.</p>
  <h2>Current model</h2>
  <p>The application uses <b>{PRODUCTION_MODEL.name}</b>, version <code>{PRODUCTION_MODEL.version}</code>, with {PRODUCTION_MODEL.representation.toLowerCase()}. See <Link to="/research">How the methods compare</Link> for validation and historical locked test evidence.</p>
  <h2>Limitations</h2>
  <p>Predictions can be wrong, miss important clauses, or lack the context needed to interpret an exception. The labels do not establish legal compliance or estimate the probability that a clause is harmful. Scanned or image-only PDFs are unsupported because OCR is not enabled. The analyzer accepts files up to 10 MB, pasted text up to 2,000,000 characters, PDFs up to 200 pages, and up to 5,000 clauses.</p>
  <h2 id="privacy">Privacy</h2>
  <p>Uploaded content is sent to the configured backend and held in a temporary server file during analysis; the file is removed afterward. The application does not keep server-side analysis history. Results are stored in session storage for the current browser tab and can be cleared from the results screen or by closing the tab.</p>
  <div className="notice">Educational screening, not legal advice. Read the complete policy and consult a qualified professional about legal matters.</div>
</section>}
