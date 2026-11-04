import { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';

import Home from './pages/HomePage';
import Analyze from './pages/AnalyzePage';
import Results from './pages/ResultsPage';
import Research from './pages/ResearchPage';
import About from './pages/AboutPage';
import ReviewPage from './pages/ReviewPage';

const RESULT_KEY = 'termsguard-analysis-result-v1';

function readSavedResult(){try{const result=JSON.parse(sessionStorage.getItem(RESULT_KEY)||'null');if(result?.extractedText)result.clauses=result.clauses.map((clause)=>({...clause,text:result.extractedText.slice(clause.startOffset,clause.endOffset)}));return result}catch{return null}}

function Site({result,setResult}){
  const location=useLocation();
  const navigate=useNavigate();
  return <><header className="nav"><Link className="brand" to="/" aria-label="TermsGuard home"><img className="site-brand-logo" src="/logo.png" alt="TermsGuard logo"/></Link><nav aria-label="Main navigation"><Link className={location.pathname==='/analyze'?'active':''} to="/analyze">Analyze</Link><Link className={location.pathname==='/research'?'active':''} to="/research">Research</Link><Link className={location.pathname==='/about'?'active':''} to="/about">How it works</Link></nav></header><Routes>
    <Route path="/" element={<Home/>}/>
    <Route path="/analyze" element={<Analyze onResult={(next)=>setResult(next)}/>}/>
    <Route path="/results" element={<Results result={result} onClear={()=>{sessionStorage.removeItem(RESULT_KEY);setResult(null)}}/>}/>
    <Route path="/example" element={<ReviewPage onNewAnalysis={()=>navigate('/analyze')}/>}/>
    <Route path="/research" element={<Research/>}/>
    <Route path="/about" element={<About/>}/>
    <Route path="*" element={<section className="panel"><h1>Page not found</h1><Link to="/">Return home</Link></section>}/>
  </Routes></>;
}

export default function App(){const[result,setResult]=useState(readSavedResult);function saveResult(next){try{const compact={...next,clauses:next.clauses.map((clause)=>({...clause,text:''}))};sessionStorage.setItem(RESULT_KEY,JSON.stringify(compact));setResult(next)}catch{setResult(null);throw new Error('Results could not be stored in this browser tab. Try a smaller document.')}}return <BrowserRouter><Site result={result} setResult={saveResult}/></BrowserRouter>}
