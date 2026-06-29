/**
 * ProtectedRoute
 * ----------------------------------------------------------
 * Guards routes that require authentication or a specific role.
 *
 * Usage:
 *   <ProtectedRoute>           // requires login only
 *   <ProtectedRoute adminOnly> // requires login + admin role
 *
 * Redirects:
 *   Not logged in  → /login   (with `from` state so login can redirect back)
 *   Logged in but wrong role → /dashboard (access denied)
 * ----------------------------------------------------------
 */

import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { isAuthenticated, isAdmin } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    // Preserve the page they were trying to reach so login can redirect back
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (adminOnly && !isAdmin) {
    // Logged in but insufficient role
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
}
