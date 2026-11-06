import { Link } from 'react-router-dom';
import { FiArrowRight, FiCheck, FiFileText, FiShield, FiSearch } from 'react-icons/fi';

export default function Home(){
  return <>
    <main>
      <section className="hero">
        <div>
          <small>POLICY REVIEW, WITH CONTEXT</small>
          <h1>Understand the fine print. <span style={{color:'#34765b'}}>Before you agree.</span></h1>
          <p>TermsGuard helps you find clauses in Terms of Service and Privacy Policies that deserve a closer look. Review model predictions alongside the original wording—not in isolation.</p>
          <div className="row">
            <Link className="button primary" to="/analyze">Analyze a document <FiArrowRight/></Link>
            <Link className="button" to="/example">Explore an example</Link>
          </div>
          <p className="muted">PDF, DOCX, TXT · Up to 10 MB · English-language screening</p>
        </div>
        <div className="paper">
          <h2>Privacy policy</h2>
          <p>We use information to provide and maintain our service.</p>
          <mark>We may share your information with advertising partners.</mark>
          <p className="muted">Risky · Illustrative classification</p>
          <div style={{display:'flex',gap:8,alignItems:'center',marginTop:24,paddingTop:17,borderTop:'1px solid #e4ebe5',fontSize:11,color:'#62766b'}}><FiShield color="#34765b"/> A prediction is a starting point—not a legal conclusion.</div>
        </div>
      </section>
      <section className="steps" aria-label="How TermsGuard works">
        <div><small>01 / ADD</small><h3>Bring your policy</h3><p>Upload a PDF, DOCX or TXT, or paste the text.</p></div>
        <div><small>02 / ANALYZE</small><h3>Find clauses to review</h3><p>See Safe, Neutral and Risky model predictions.</p></div>
        <div><small>03 / UNDERSTAND</small><h3>Keep the context</h3><p>Jump from a prediction to its original wording.</p></div>
      </section>
      <section style={{maxWidth:1100,margin:'30px auto 65px',padding:'0 28px'}}>
        <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:17,color:'#557565',fontSize:11,fontWeight:700,letterSpacing:1}}><FiSearch/> BUILT FOR CAREFUL REVIEW</div>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(210px,1fr))',gap:14}}>
          <Feature icon={<FiFileText/>} title="Clause-level results" text="Review individual passages instead of treating an entire policy as one score."/>
          <Feature icon={<FiShield/>} title="Context stays visible" text="Read model-flagged wording in the surrounding document text."/>
          <Feature icon={<FiCheck/>} title="Transparent methodology" text="Explore model comparisons, validation metrics and known limitations."/>
        </div>
      </section>
    </main>
    <footer>Educational screening, not legal advice. Always read the complete policy.</footer>
  </>;
}
function Feature({icon,title,text}){return <article style={{padding:'20px 21px',background:'#fff',border:'1px solid #dfe8e1',borderRadius:13}}><div style={{width:34,height:34,display:'grid',placeItems:'center',borderRadius:9,background:'#eaf1eb',color:'#24634d',marginBottom:13}}>{icon}</div><h3 style={{fontSize:14,margin:'0 0 7px'}}>{title}</h3><p style={{fontSize:12,color:'#64776d',lineHeight:1.7,margin:0}}>{text}</p></article>}
