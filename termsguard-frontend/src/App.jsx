import { useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { FiFileText } from 'react-icons/fi';
import Home from './pages/HomePage';
import Analyze from './pages/AnalyzePage';
import Results from './pages/ResultsPage';
import Research from './pages/ResearchPage';
import About from './pages/AboutPage';
import ReviewPage from './pages/ReviewPage';

export default function App(){const[result,setResult]=useState(null);return <BrowserRouter><header className="nav"><Link className="brand" to="/"><FiFileText/>TermsGuard</Link><nav><Link to="/analyze">Analyze</Link><Link to="/research">Research</Link><Link to="/about">How it works</Link></nav></header><Routes><Route path="/" element={<Home/>}/><Route path="/analyze" element={<Analyze onResult={setResult}/>}/><Route path="/results" element={<Results result={result}/>}/><Route path="/example" element={<ReviewPage onNewAnalysis={()=>location.assign('/analyze')}/>}/><Route path="/research" element={<Research/>}/><Route path="/about" element={<About/>}/><Route path="*" element={<section className="panel"><h1>Page not found</h1><Link to="/">Return home</Link></section>}/></Routes></BrowserRouter>}
