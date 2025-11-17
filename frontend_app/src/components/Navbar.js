import { NavLink } from "react-router-dom";
import "./Navbar.css"; // We will create this CSS file next

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <NavLink to="/" className="navbar-logo">
          ArXiv KG Explorer
        </NavLink>
        <ul className="nav-menu">
          <li className="nav-item">
            <NavLink
              to="/shared-effects"
              className="nav-links"
              activeClassName="active"
            >
              Shared Effects
            </NavLink>
          </li>
          <li className="nav-item">
            <NavLink
              to="/causal-chains"
              className="nav-links"
              activeClassName="active"
            >
              Causal Chains
            </NavLink>
          </li>
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;
