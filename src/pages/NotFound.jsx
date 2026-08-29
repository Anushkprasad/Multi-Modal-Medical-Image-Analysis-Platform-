import { Link } from 'react-router-dom';
import './NotFound.css';

const NotFound = () => {
  return (
    <div className="notfound-page">
      <div className="notfound-card">
        <h1 className="notfound-code">404</h1>
        <h2 className="notfound-title">Page Not Found</h2>
        <p className="notfound-text">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link to="/" className="notfound-button">
          Go Back Home
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
