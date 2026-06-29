import { NavLink, useNavigate } from "react-router-dom";
import { ShieldHalf, LogOut, Settings } from "lucide-react";
import ThemeToggle from "../ui/ThemeToggle";
import { useAuth } from "../../context/AuthContext";

const PUBLIC_NAV = [
  { to: "/", label: "Home", end: true },
  { to: "/about", label: "About" },
];

const AUTH_NAV = [
  { to: "/analysis", label: "Analysis" },
  { to: "/dashboard", label: "Dashboard" },
];

const ADMIN_NAV = [
  { to: "/admin", label: "Admin" },
];

export default function Navbar() {
  const { isAuthenticated, isAdmin, currentUser, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const navLinks = [
    ...PUBLIC_NAV,
    ...(isAuthenticated ? AUTH_NAV : []),
    ...(isAdmin ? ADMIN_NAV : []),
  ];

  return (
    <header
      className="sticky top-0 z-50 border-b backdrop-blur-md"
      style={{ backgroundColor: "color-mix(in srgb, var(--color-bg) 85%, transparent)" }}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <NavLink to="/" className="flex items-center gap-2 focus-ring rounded-md">
          <ShieldHalf size={20} strokeWidth={2.25} style={{ color: "var(--color-accent)" }} />
          <span className="font-mono text-[15px] font-semibold tracking-tight" style={{ color: "var(--color-text-primary)" }}>
            PsychShield
          </span>
        </NavLink>

        <nav className="hidden items-center gap-1 sm:flex">
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                `focus-ring rounded-md px-3 py-2 text-sm font-medium transition-colors ${isActive ? "" : "hover:opacity-80"}`
              }
              style={({ isActive }) => ({
                color: isActive ? "var(--color-accent)" : "var(--color-text-secondary)",
                backgroundColor: isActive ? "var(--color-accent-soft)" : "transparent",
              })}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          {isAuthenticated && (
            <>
              <NavLink
                to="/settings"
                className="focus-ring rounded-md p-2 transition-colors hover:opacity-80"
                style={{ color: "var(--color-text-secondary)" }}
                aria-label="Settings"
              >
                <Settings size={17} />
              </NavLink>
              <div
                className="hidden sm:flex items-center gap-2 rounded-lg border px-3 py-1.5"
                style={{ borderColor: "var(--color-border)", backgroundColor: "var(--color-bg-sunken)" }}
              >
                <span className="text-xs font-mono" style={{ color: "var(--color-text-secondary)" }}>
                  {currentUser?.name}
                </span>
                <span
                  className="rounded px-1.5 py-0.5 text-[10px] font-mono font-semibold capitalize"
                  style={{ backgroundColor: "var(--color-accent-soft)", color: "var(--color-accent)" }}
                >
                  {currentUser?.role}
                </span>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="focus-ring rounded-md p-2 transition-colors hover:opacity-80"
                style={{ color: "var(--color-text-secondary)" }}
                aria-label="Sign out"
              >
                <LogOut size={17} />
              </button>
            </>
          )}
          {!isAuthenticated && (
            <div className="flex items-center gap-2">
              <NavLink
                to="/signup"
                className="focus-ring rounded-lg border px-4 py-2 text-sm font-semibold transition-colors hover:opacity-80"
                style={{ borderColor: "var(--color-border-strong)", color: "var(--color-text-primary)" }}
              >
                Sign up
              </NavLink>
              <NavLink
                to="/login"
                className="focus-ring rounded-lg px-4 py-2 text-sm font-semibold"
                style={{ backgroundColor: "var(--color-accent)", color: "var(--color-bg-elevated)" }}
              >
                Sign in
              </NavLink>
            </div>
          )}
        </div>
      </div>

      {/* Mobile nav */}
      <nav className="flex items-center gap-1 overflow-x-auto border-t px-4 py-2 sm:hidden">
        {navLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className="focus-ring shrink-0 rounded-md px-3 py-1.5 text-sm font-medium"
            style={({ isActive }) => ({
              color: isActive ? "var(--color-accent)" : "var(--color-text-secondary)",
              backgroundColor: isActive ? "var(--color-accent-soft)" : "transparent",
            })}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
