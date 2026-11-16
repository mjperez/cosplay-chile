import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './contexto/AuthContext'
import { MetaProvider } from './contexto/MetaContext'
// Tipografías autoalojadas (sin solicitudes a Google Fonts): latín y latín extendido
import '@fontsource/dm-sans/latin-400.css'
import '@fontsource/dm-sans/latin-500.css'
import '@fontsource/dm-sans/latin-700.css'
import '@fontsource/dm-sans/latin-ext-400.css'
import '@fontsource/dm-sans/latin-ext-700.css'
import '@fontsource/playfair-display/latin-600.css'
import '@fontsource/playfair-display/latin-700.css'
import '@fontsource/playfair-display/latin-800.css'
import '@fontsource/playfair-display/latin-ext-700.css'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <MetaProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MetaProvider>
    </BrowserRouter>
  </StrictMode>,
)
