import { Link } from "react-router-dom";
import "./Navbar.css";
function Navbar() {
  return (
    <nav className="navbar">
      {/* <div className="navbar-title">
        Multi-Modal Medical Image Analysis Platform
      </div> */}

      <div className="navbar-links">
        <Link className="navbar-link" to="/">
          Home
        </Link>
      </div>
    </nav>
  );
}

export default Navbar;
