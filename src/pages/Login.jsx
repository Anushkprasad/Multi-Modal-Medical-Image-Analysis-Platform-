import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import './Login.css';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email || !password || (isRegister && !name)) {
      toast.error('Please fill in all fields');
      return;
    }

    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      const token = 'mock-jwt-token';
      const user = { email, name: isRegister ? name : email.split('@')[0] };
      
      localStorage.setItem('med_token', token);
      localStorage.setItem('med_user', JSON.stringify(user));
      
      toast.success(isRegister ? 'Registration successful!' : 'Login successful!');
      setLoading(false);
      navigate('/');
    }, 1000);
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h1>🏥 MedAI Platform</h1>
          <p>{isRegister ? 'Create an account to continue' : 'Welcome back, please login to your account'}</p>
        </div>
        
        <form className="login-form" onSubmit={handleSubmit}>
          {isRegister && (
            <div className="form-group">
              <label htmlFor="name">Full Name</label>
              <input
                type="text"
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
              />
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="doctor@hospital.com"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>
          
          <button 
            type="submit" 
            className={`login-button ${loading ? 'loading' : ''}`}
            disabled={loading}
          >
            {loading ? 'Processing...' : (isRegister ? 'Register' : 'Login')}
          </button>
        </form>
        
        <div className="login-toggle" onClick={() => setIsRegister(!isRegister)}>
          {isRegister ? 'Already have an account? Log in' : "Don't have an account? Register"}
        </div>
      </div>
    </div>
  );
};

export default Login;
