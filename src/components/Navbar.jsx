import { Link, useNavigate } from "react-router-dom";
import useAuth from "../hooks/useAuth";
import { useTheme } from "../contexts/ThemeContext";
import "./Navbar.css";

function Navbar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <div className="navbar-logo">
        <Link to="/" className="navbar-brand">
          <span className="logo-icon">🏥</span> MedAI Platform
        </Link>
      </div>

      <div className="navbar-menu">
        <div className="navbar-links">
          <Link className="navbar-link" to="/">
            Home
          </Link>
          {user && (
            <>
              <Link className="navbar-link" to="/upload">
                New Scan
              </Link>
              <Link className="navbar-link" to="/history">
                History
              </Link>
            </>
          )}
        </div>

        <div className="navbar-actions">
          {/* Theme Toggle Button */}
          <button
            className="theme-toggle-btn"
            onClick={toggleTheme}
            title={`Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`}
          >
            {theme === "dark" ? "☀️" : "🌙"}
          </button>

          {user ? (
            <div className="user-profile">
              <span className="user-name">Hello, {user.name || "Doctor"}</span>
              <button className="logout-btn" onClick={handleLogout}>
                Logout
              </button>
            </div>
          ) : (
            <Link className="login-btn-nav" to="/login">
              Login
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
