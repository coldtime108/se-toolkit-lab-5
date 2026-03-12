import { useState, useEffect } from 'react';
import Items from './Items';
import Dashboard from './Dashboard';
import Login from './Login';
import './App.css';

function App() {
  const [page, setPage] = useState<'items' | 'dashboard'>('items');
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('api_key');
    setIsAuthenticated(!!token);
  }, []);

  const handleLogin = (token: string) => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('api_key');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="App">
      <header style={{ padding: '10px', background: '#f0f0f0', marginBottom: '20px' }}>
        <button onClick={() => setPage('items')} style={{ marginRight: '10px' }}>Items</button>
        <button onClick={() => setPage('dashboard')} style={{ marginRight: '10px' }}>Dashboard</button>
        <button onClick={handleLogout}>Logout</button>
      </header>

      {page === 'items' ? <Items /> : <Dashboard />}
    </div>
  );
}

export default App;
