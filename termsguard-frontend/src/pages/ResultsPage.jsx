import { Link, useNavigate } from 'react-router-dom';
import ReviewPage from './ReviewPage';

export default function Results({result}){const navigate=useNavigate();return result?<ReviewPage documentData={result} illustrative={false} onNewAnalysis={()=>navigate('/analyze')}/>:<section className="panel"><h1>No analysis to display</h1><p>Results are held in memory and are cleared when this page reloads.</p><Link className="button primary" to="/analyze">Analyze a document</Link></section>}
