import React from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';

function App() {
  // Simple client-side routing
  const path = window.location.pathname;
  const isLoggedIn = true; // This should be replaced with actual auth state

  // If logged in, show dashboard
  if (isLoggedIn && path !== '/login' && path !== '/register') {
    return <Dashboard />;
  }

  // Otherwise show public pages
  return (
    <div className="min-h-screen bg-white">
      {path === '/login' ? (
        <Login />
      ) : path === '/register' ? (
        <Register />
      ) : (
        <>
          <Header />
          <Hero />
        </>
      )}
    </div>
  );
}

export default App;