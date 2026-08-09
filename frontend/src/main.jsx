import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'
import App from './App.jsx'
import CourtSniperProvider from './context/CourtSniperProvider.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <CourtSniperProvider>
      <App />
    </CourtSniperProvider>
  </StrictMode>,
)
