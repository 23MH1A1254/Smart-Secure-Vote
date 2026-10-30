import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

const api = async (path, options={}) => {
  const r = await fetch('/api'+path, {headers:{'Content-Type':'application/json'}, ...options})
  const data = await r.json().catch(()=>({detail:'Unexpected server response'}))
  if (!r.ok) throw new Error(data.detail || 'Request failed')
  return data
}
function App() {
  const [page,setPage]=useState('home'), [voter,setVoter]=useState(''), [otp,setOtp]=useState(''), [demoOtp,setDemoOtp]=useState(''), [candidates,setCandidates]=useState([]), [candidate,setCandidate]=useState(''), [message,setMessage]=useState(''), [receipt,setReceipt]=useState('')
  const [username,setUsername]=useState('admin'), [password,setPassword]=useState('')
  const loadCandidates=()=>api('/candidates').then(setCandidates).catch(e=>setMessage(e.message))
  useEffect(()=>{loadCandidates()},[])
  const run=async fn=>{setMessage('');try{await fn()}catch(e){setMessage(e.message)}}
  const verify=()=>run(async()=>{const d=await api('/voter/verify',{method:'POST',body:JSON.stringify({voter_id:voter})});setDemoOtp(d.demo_otp||'');setPage('otp');setMessage(d.message)})
  const check=()=>run(async()=>{await api('/voter/otp',{method:'POST',body:JSON.stringify({voter_id:voter,otp})});setPage('vote');setMessage('Identity verified. Select your candidate.')})
  const vote=()=>run(async()=>{const d=await api('/voter/vote',{method:'POST',body:JSON.stringify({voter_id:voter,candidate_id:Number(candidate)})});setReceipt(d.receipt);setPage('done')})
  const admin=()=>run(async()=>{await api('/admin/login',{method:'POST',body:JSON.stringify({username,password})});setPage('admin');loadCandidates()})
  return <div className="shell"><header><div className="brand">🔐 Smart Secure Vote</div><nav><button onClick={()=>setPage('home')}>Home</button><button onClick={()=>{setPage('adminLogin');setMessage('')}}>Admin</button></nav></header>
  <main><section className="hero"><p className="eyebrow">SECURE • SIMPLE • TRANSPARENT</p><h1>Your vote matters.<br/><span>Your security matters more.</span></h1><p>A student project demo featuring voter ID verification, one-time passwords and one-vote protection.</p></section>
  {message&&<div className="notice">{message}</div>}
  {page==='home'&&<section className="panel"><h2>Cast your vote</h2><p>Enter your pre-registered voter ID to begin.</p><input placeholder="Example: VOT1001" value={voter} onChange={e=>setVoter(e.target.value.toUpperCase())}/><button className="primary" onClick={verify}>Verify voter ID</button><small>Demo voter IDs: VOT1001 – VOT1008</small></section>}
  {page==='otp'&&<section className="panel"><h2>OTP verification</h2><p>Enter the six-digit code sent to your registered phone.</p>{demoOtp&&<div className="demo">Demo OTP: <b>{demoOtp}</b></div>}<input maxLength="6" placeholder="6-digit OTP" value={otp} onChange={e=>setOtp(e.target.value)}/><button className="primary" onClick={check}>Verify OTP</button></section>}
  {page==='vote'&&<section className="panel"><h2>Select your candidate</h2>{candidates.map(c=><label className="candidate" key={c.id}><input type="radio" name="candidate" value={c.id} checked={candidate===String(c.id)} onChange={e=>setCandidate(e.target.value)}/><span><b>{c.name}</b><small>{c.party}</small></span></label>)}<button className="primary" disabled={!candidate} onClick={vote}>Confirm vote</button><small>Your vote cannot be changed after submission.</small></section>}
  {page==='done'&&<section className="panel success"><h2>✓ Vote recorded</h2><p>Thank you for participating in this demo election.</p><div className="receipt">Receipt: {receipt}</div><button onClick={()=>{setPage('home');setVoter('');setOtp('');setCandidate('');setDemoOtp('')}}>Back to home</button></section>}
  {page==='adminLogin'&&<section className="panel"><h2>Administrator login</h2><input placeholder="Username" value={username} onChange={e=>setUsername(e.target.value)}/><input type="password" placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)}/><button className="primary" onClick={admin}>Login</button><small>Demo default: admin / ChangeMe-Demo-123 (change before use)</small></section>}
  {page==='admin'&&<section className="panel"><h2>Admin dashboard</h2><button onClick={()=>run(async()=>{const r=await api('/admin/results');setMessage(r.map(x=>`${x.candidate}: ${x.votes} votes`).join(' | ')||'No results')})}>View results</button><h3>Candidates</h3>{candidates.map(c=><p key={c.id}>{c.name} — {c.party}</p>)}<button onClick={()=>setPage('home')}>Exit admin</button></section>}
  <footer>Academic demonstration only · Not for real elections</footer></main></div>
}
createRoot(document.getElementById('root')).render(<App/>)
