import { useState } from 'react';

interface LoginProps {
  onLogin: (token: string) => void;
}

function Login({ onLogin }: LoginProps) {
  const [apiKey, setApiKey] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (apiKey.trim()) {
      localStorage.setItem('api_key', apiKey.trim());
      onLogin(apiKey.trim());
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '50px auto', padding: '20px', border: '1px solid #ccc' }}>
      <h2>Enter API Key</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="Your API key"
          style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
        />
        <button type="submit" style={{ padding: '8px 16px' }}>Login</button>
      </form>
    </div>
  );
}

export default Login;
