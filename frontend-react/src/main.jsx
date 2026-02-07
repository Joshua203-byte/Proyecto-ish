import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {console.log("Epochly v38 Loaded")}
    <App />
  </StrictMode>,
)
// Build 1770306007
