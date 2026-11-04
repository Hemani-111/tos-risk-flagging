import { useMemo, useState } from 'react';
import { COMPARISON_ROWS, PRODUCTION_MODEL } from '../lib/comparisonData.ts';

const protocols = [
  { key: 'Primary', label: 'Unseen-service', description: 'Services are held out between training and evaluation to estimate performance on services absent from training.' },
  { key: 'Clause', label: 'Duplicate-aware clause', description: 'Normalized duplicate clauses are kept together across partitions to reduce text overlap.' },
];

export default function Research(){
  const [protocol,setProtocol]=useState('Primary');
  const rows=useMemo(()=>COMPARISON_ROWS.filter((row)=>row.protocol===protocol),[protocol]);
  return <main className="panel information-panel research-panel">
    <small>MODEL EVIDENCE</small><h1>How the methods compare.</h1>
    <p>Eight text classification methods were trained and compared using fixed data partitions. Macro F1 summarizes performance across the three labels; Risky precision and recall show how often Risky predictions were correct and how many Risky examples were found.</p>
    <div className="protocol-tabs" role="tablist" aria-label="Evaluation protocol">{protocols.map((item)=><button key={item.key} role="tab" aria-selected={protocol===item.key} onClick={()=>setProtocol(item.key)}>{item.label}</button>)}</div>
    <p className="protocol-description">{protocols.find((item)=>item.key===protocol)?.description} The table reports held-out validation results separately from tuning cross validation.</p>
    <section className="research-chart"><h2>Validation macro F1</h2>{rows.map((row)=><div className="research-bar" key={row.model}><span>{row.model}</span><div><i className={row.status==='Production model'?'production':''} style={{width:`${Number(row.valMacroF1)*100}%`}}/></div><b>{row.valMacroF1}</b></div>)}</section>
    <section className="research-table"><h2>Model comparison</h2><div className="research-table-scroll"><table><thead><tr><th>Model</th><th>Representation</th><th>Validation macro F1</th><th>Risky precision</th><th>Risky recall</th></tr></thead><tbody>{rows.map((row)=><tr key={row.model} className={row.status==='Production model'?'deployed':''}><td><details><summary>{row.model}{row.status==='Production model'&&<span className="deployed-tag">Deployed</span>}</summary><p>{row.config}<br/>Tuning CV macro F1: {row.cvMacroF1} ± {row.cvMacroF1Std}<br/>Accuracy: {row.accuracy} · Balanced accuracy: {row.balancedAccuracy}<br/>Fit: {row.fitSeconds}s · Prediction: {row.predictSeconds}s</p></details></td><td>{row.representation}</td><td>{row.valMacroF1}</td><td>{row.riskyPrecision}</td><td>{row.riskyRecall}</td></tr>)}</tbody></table></div></section>
    <section className="locked-test"><h2>Historical locked test evidence</h2><p>The candidate was frozen before these metrics were calculated. Earlier development runs materialized the full source data, including test rows, through a shared loader, but no test metrics were viewed then. The results are reported transparently; the set is not described as untouched.</p><div className="research-table-scroll"><table><thead><tr><th>Protocol</th><th>Test clauses</th><th>Macro F1</th><th>Risky precision</th><th>Risky recall</th></tr></thead><tbody><tr><td>Unseen-service</td><td>2,585</td><td>0.8358</td><td>0.8229</td><td>0.8287</td></tr><tr><td>Duplicate-aware clause</td><td>2,602</td><td>0.8144</td><td>0.7922</td><td>0.8117</td></tr></tbody></table></div><p>These scores measure annotated clause classification, not complete-policy understanding. Risky misses remain. Full intervals and disclosure are in <code>docs/LOCKED_TEST_EVALUATION_v1.md</code>.</p></section>
    <div className="notice"><b>Deployed artifact:</b> {PRODUCTION_MODEL.name}, <code>{PRODUCTION_MODEL.version}</code>, at <code>{PRODUCTION_MODEL.path}</code>. Validation scores are not probabilities or guarantees for future documents.</div>
  </main>
}
