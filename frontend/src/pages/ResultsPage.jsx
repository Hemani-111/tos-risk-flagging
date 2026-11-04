import { Link, useNavigate } from 'react-router-dom';
import ReviewPage from './ReviewPage';

export default function Results({ result, onClear }) {
  const navigate = useNavigate();
  return result
    ? <ReviewPage documentData={result} illustrative={false} onNewAnalysis={() => navigate('/analyze')} onClear={onClear}/>
    : <section className="panel"><small>DOCUMENT REVIEW</small><h1>No analysis to display</h1><p>Results are kept in this browser tab. Start a new analysis to review a document.</p><Link className="button primary" to="/analyze">Analyze a document</Link></section>;
}
