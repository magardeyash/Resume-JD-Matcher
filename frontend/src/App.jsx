import React, { useState, useEffect } from 'react';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Banner from './components/Banner';
import Dashboard from './pages/Dashboard';
import Results from './pages/Results';
import History from './pages/History';
import Login from './pages/Login';
import Register from './pages/Register';

function AppContent() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname || '/');

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname || '/');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (path) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  let pageContent;
  if (currentPath === '/login') {
    pageContent = <Login onNavigate={navigate} />;
  } else if (currentPath === '/register') {
    pageContent = <Register onNavigate={navigate} />;
  } else if (currentPath === '/history') {
    pageContent = <History onNavigate={navigate} />;
  } else if (currentPath.startsWith('/results/')) {
    const analysisId = currentPath.replace('/results/', '');
    pageContent = <Results analysisId={analysisId} onNavigate={navigate} />;
  } else {
    pageContent = <Dashboard onNavigate={navigate} />;
  }

  return (
    <>
      <Navbar currentPath={currentPath} onNavigate={navigate} />
      <Banner onNavigate={navigate} />
      {pageContent}
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
