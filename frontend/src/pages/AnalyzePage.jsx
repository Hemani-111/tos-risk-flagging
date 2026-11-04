import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiFileText, FiUploadCloud, FiX } from 'react-icons/fi';
import { request, normalize } from '../lib/api';

const MAX_BYTES = 10 * 1024 * 1024;
const MAX_TEXT = 2_000_000;
const MIN_TEXT = 50;

export default function Analyze({ onResult }) {
  const [mode, setMode] = useState('file');
  const [file, setFile] = useState(null);
  const [text, setText] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const fileInput = useRef(null);
  const navigate = useNavigate();

  function choose(nextFile) {
    if (!nextFile) return;
    const extension = nextFile.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'txt'].includes(extension)) { setError('Choose a PDF, DOCX, or TXT file.'); return; }
    if (nextFile.size > MAX_BYTES) { setError('The file exceeds the 10 MB upload limit.'); return; }
    setFile(nextFile);
    setError('');
  }

  async function submit(event) {
    event.preventDefault();
    setError('');
    if (mode === 'file' && !file) { setError('Choose a document first.'); return; }
    if (mode === 'text' && text.trim().length < MIN_TEXT) { setError(`Enter at least ${MIN_TEXT} characters.`); return; }
    setBusy(true);
    try {
      let data;
      if (mode === 'file') {
        const body = new FormData(); body.append('file', file);
        data = await request('/api/v1/documents/analyze', { method: 'POST', body });
      } else {
        data = await request('/api/v1/documents/analyze-text', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: text.trim() }) });
      }
      onResult(normalize(data));
      navigate('/results');
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Analysis failed. Your input is still here; please retry.');
    } finally { setBusy(false); }
  }

  return <main className="analyze-page">
    <section className="hero analyze-hero">
      <div className="analyze-copy"><small>DOCUMENT ANALYSIS</small><h1>Bring the fine print.</h1><p>Upload a Terms of Service or Privacy Policy, or paste its text to review model predictions in context.</p><p className="muted">PDF, DOCX, TXT · Up to 10 MB · English-language screening</p></div>
      <section className="upload-card" aria-label="Add a document">
        <div className="upload-heading"><span><FiFileText/></span><div><h2>Add a document</h2><p>Choose a file or paste policy text.</p></div></div>
        <div className="input-tabs" role="tablist" aria-label="Document input method"><button type="button" role="tab" aria-selected={mode === 'file'} className={mode === 'file' ? 'active' : ''} disabled={busy} onClick={() => { setMode('file'); setError(''); }}>Upload file</button><button type="button" role="tab" aria-selected={mode === 'text'} className={mode === 'text' ? 'active' : ''} disabled={busy} onClick={() => { setMode('text'); setError(''); }}>Paste text</button></div>
        <form onSubmit={submit}>
          {mode === 'file' ? <>
            <input ref={fileInput} className="visually-hidden" type="file" accept=".pdf,.docx,.txt" disabled={busy} onChange={(event) => { choose(event.target.files?.[0]); event.currentTarget.value = ''; }}/>
            <div className={`drop ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setDragging(false); }} onDrop={(event) => { event.preventDefault(); setDragging(false); if (!busy) choose(event.dataTransfer.files?.[0]); }}>
              {file ? <><FiFileText size={30}/><strong className="selected-filename">{file.name}</strong><span className="file-size">{file.name.split('.').pop()?.toUpperCase()} · {(file.size / 1024 / 1024).toFixed(2)} MB</span><div className="file-actions"><button type="button" disabled={busy} onClick={() => fileInput.current?.click()}>Replace file</button><button type="button" disabled={busy} aria-label="Remove file" onClick={() => { setFile(null); setError(''); }}><FiX/> Remove</button></div></> : <><FiUploadCloud size={34}/><strong>Drop your document here</strong><p>or choose a file from your device</p><button type="button" onClick={() => fileInput.current?.click()} disabled={busy}>Choose file</button><span className="file-size">PDF, DOCX, TXT · Maximum 10 MB</span></>}
            </div>
          </> : <div className="paste-input"><label htmlFor="policy">Policy text</label><textarea id="policy" value={text} maxLength={MAX_TEXT} disabled={busy} onChange={(event) => setText(event.target.value)} placeholder="Paste or type the policy text you want to review…"/><div className="text-counter"><span>{text.length.toLocaleString()} / {MAX_TEXT.toLocaleString()} characters</span><span>Minimum {MIN_TEXT}</span></div></div>}
          {error && <p role="alert" className="error">{error}</p>}
          <p className="privacy-copy">Files are sent to the configured backend for analysis and removed from temporary storage afterward. Results remain in this browser tab’s session storage. <a href="/about#privacy">Privacy details</a></p>
          <button className="primary analyze-submit" disabled={busy || (mode === 'file' && !file) || (mode === 'text' && text.trim().length < MIN_TEXT)}>{busy ? 'Analyzing document…' : 'Analyze document'}</button>
          {busy && <p className="loading-note" aria-live="polite">Your input stays here while analysis runs. This may take a moment.</p>}
        </form>
      </section>
    </section>
    <section className="steps analyze-steps"><div><small>01 / ADD</small><h3>Start with your policy</h3><p>Choose a document or paste its text.</p></div><div><small>02 / FIND</small><h3>See clause predictions</h3><p>Browse Safe, Neutral, and Risky labels.</p></div><div><small>03 / REVIEW</small><h3>Keep the context</h3><p>Jump from each finding to its source wording.</p></div></section>
  </main>;
}
