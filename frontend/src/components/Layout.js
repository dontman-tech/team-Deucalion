import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Layout.css';

function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [language, setLanguage] = useState('en');

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleLanguageChange = (e) => {
    setLanguage(e.target.value);
    localStorage.setItem('preferred_language', e.target.value);
  };

  const getNavItems = () => {
    const basePath = user?.userType || '';
    return [
      { path: `/${basePath}`, label: 'Dashboard', icon: '🏠' },
      { path: '/ai-chat', label: 'AI Tutor', icon: '🤖' },
      { path: '/join-class', label: 'Join Class', icon: '📚' }
    ];
  };

  const navItems = getNavItems();

  return (
    <div className="page-layout">
      <aside className="sidebar">
        <Link to="/" className="logo">LUMINA</Link>
        <nav>
          <ul className="nav-menu">
            {navItems.map(item => (
              <li key={item.path} className="nav-item">
                <Link
                  to={item.path}
                  className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
                >
                  <span className="icon">{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      </aside>
      <main className="main-content">
        <header className="top-header">
          <div className="header-right">
            <select 
              value={language} 
              onChange={handleLanguageChange}
              className="language-select"
            >
              <option value="en">🇬🇧 EN</option>
              <option value="fr">🇫🇷 FR</option>
            </select>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
