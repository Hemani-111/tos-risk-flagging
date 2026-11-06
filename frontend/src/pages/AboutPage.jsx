import { Link } from 'react-router-dom';
import { FiFileText, FiScissors, FiGrid, FiTarget, FiAlertCircle } from 'react-icons/fi';
import { PRODUCTION_MODEL } from '../lib/comparisonData';

const stages=[
  {n:'01',icon:<FiFileText/>,title:'Extract text',body:'The analyzer reads text from supported PDF, DOCX and TXT documents. Scanned or image-only PDFs are not supported because OCR is not enabled.'},
  {n:'02',icon:<FiScissors/>,title:'Segment clauses',body:'Extracted text is divided into individual clauses so that predictions can be reviewed at a useful level of detail.'},
  {n:'03',icon:<FiGrid/>,title:'Build text features',body:'Word and phrase patterns are represented using TF-IDF features, including unigram and bigram information.'},
  {n:'04',icon:<FiTarget/>,title:'Classify each clause',body:`The deployed ${PRODUCTION_MODEL.name} model predicts whether each clause resembles Safe, Neutral or Risky examples from its training data.`},
];
export default function About(){return <main className="panel information-panel">
  <small>HOW IT WORKS</small><h1>Read the wording.<br/>Use labels as a starting point.</h1>
  <p>TermsGuard is an educational text-screening tool. It extracts a document’s text, splits it into clauses and assigns a model prediction to each clause. The results are designed to help you decide what to read more carefully.</p>
  <section style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(165px,1fr))',gap:10,margin:'24px 0 30px'}}>{stages.map(s=><article key={s.n} style={{padding:15,border:'1px solid #dfe8e1',borderRadius:10,background:'#fbfcfa'}}><div style={{display:'flex',alignItems:'center',gap:8,color:'#34765b',fontSize:11,fontWeight:700}}>{s.icon}{s.n}</div><h3 style={{fontSize:14,margin:'11px 0 6px'}}>{s.title}</h3><p style={{fontSize:11,lineHeight:1.65,margin:0}}>{s.body}</p></article>)}</section>
  <h2>What the labels mean</h2>
  <div style={{display:'grid',gap:9}}>
    <Label color="#2f7650" bg="#e5f2e9" name="Safe" text="Predicted to resemble protective examples in the training data. This is a classification label, not a guarantee."/>
    <Label color="#8a671f" bg="#faf2dd" name="Neutral" text="Predicted to resemble neutral examples in the training data."/>
    <Label color="#9a4943" bg="#fae9e6" name="Risky" text="Predicted to resemble adverse examples in the training data. Read the full clause and surrounding context."/>
  </div>
  <h2>Current model</h2>
  <p>The application uses <b>{PRODUCTION_MODEL.name}</b>, version <code>{PRODUCTION_MODEL.version}</code>, with {PRODUCTION_MODEL.representation.toLowerCase()}. See <Link to="/research">How the methods compare</Link> for validation and historical locked test evidence.</p>
  <h2>Limitations</h2>
  <p>Predictions can be wrong, miss important clauses, or lack the context needed to interpret an exception. The labels do not establish legal compliance or estimate the probability that a clause is harmful. Scanned or image-only PDFs are unsupported because OCR is not enabled. The analyzer accepts files up to 10 MB, pasted text up to 2,000,000 characters, PDFs up to 200 pages, and up to 5,000 clauses.</p>
  <h2 id="privacy">Privacy</h2>
  <p>Uploaded content is sent to the configured backend and held in a temporary server file during analysis; the file is removed afterward. The application does not keep server-side analysis history. Results are stored in session storage for the current browser tab and can be cleared from the results screen or by closing the tab.</p>
  <div className="notice"><b><FiAlertCircle style={{verticalAlign:'-2px',marginRight:6}}/>Educational screening, not legal advice.</b> Read the complete policy and consult a qualified professional about legal matters.</div>
</main>}
function Label({color,bg,name,text}){return <div style={{display:'grid',gridTemplateColumns:'82px 1fr',gap:12,alignItems:'start',padding:'11px 13px',background:bg,borderRadius:8}}><b style={{fontSize:12,color}}>{name}</b><span style={{fontSize:12,color:'#52665b',lineHeight:1.6}}>{text}</span></div>}
