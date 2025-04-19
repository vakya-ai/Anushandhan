// src/App.jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { ChatHistoryProvider } from './context/ChatHistoryContext';
import LandingPage from './components/LandingPage';
import ResearchPaperGenerator from './components/ResearchPaperGenerator';

function App() {
  const GOOGLE_CLIENT_ID = "659488376689-9pr3mtcctlk8d9ot7rbpge0ulmqjke81.apps.googleusercontent.com"; // Replace with your actual Google Client ID

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <ChatHistoryProvider>
        <Router>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/generator" element={<ResearchPaperGenerator />} />
          </Routes>
        </Router>
      </ChatHistoryProvider>
    </GoogleOAuthProvider>
  );
}

export default App;