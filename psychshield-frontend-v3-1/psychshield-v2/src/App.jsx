import { Routes, Route } from "react-router-dom";
import Navbar from "./components/layout/Navbar";
import Footer from "./components/layout/Footer";
import ProtectedRoute from "./components/ui/ProtectedRoute";

// Public pages
import Landing from "./pages/Landing";
import About from "./pages/About";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Unauthorized from "./pages/Unauthorized";

// Protected pages (require login)
import EmailAnalysis from "./pages/EmailAnalysis";
import Dashboard from "./pages/Dashboard";
import Settings from "./pages/Settings";

// Admin-only pages (require login + admin role)
import AdminPanel from "./pages/AdminPanel";

/**
 * App — root routing and layout shell.
 *
 * Route structure:
 *   Public:    /  /about  /login  /unauthorized
 *   Protected: /analysis  /dashboard  /settings
 *   Admin:     /admin
 *
 * Login page uses its own minimal layout (no Navbar/Footer)
 * so it's rendered outside the shared shell.
 */
export default function App() {
  return (
    <Routes>
      {/* Login and Signup have their own layout — no Navbar or Footer */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      {/* All other pages share the Navbar + Footer shell */}
      <Route
        path="*"
        element={
          <div className="flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1">
              <Routes>
                {/* Public */}
                <Route path="/" element={<Landing />} />
                <Route path="/about" element={<About />} />
                <Route path="/unauthorized" element={<Unauthorized />} />

                {/* Protected — login required */}
                <Route path="/analysis" element={
                  <ProtectedRoute><EmailAnalysis /></ProtectedRoute>
                } />
                <Route path="/dashboard" element={
                  <ProtectedRoute><Dashboard /></ProtectedRoute>
                } />
                <Route path="/settings" element={
                  <ProtectedRoute><Settings /></ProtectedRoute>
                } />

                {/* Admin only */}
                <Route path="/admin" element={
                  <ProtectedRoute adminOnly><AdminPanel /></ProtectedRoute>
                } />
              </Routes>
            </main>
            <Footer />
          </div>
        }
      />
    </Routes>
  );
}
