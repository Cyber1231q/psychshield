/**
 * AuthContext
 * ----------------------------------------------------------
 * Manages authentication state for PsychShield.
 * - Stores JWT token in memory only (never localStorage) for security
 * - Exposes login(), register(), logout(), and currentUser to all components
 * - Wired to POST /api/auth/login and /api/auth/register on FastAPI backend
 *
 * ROLES:
 *   admin   -> full access: Admin Panel, Dashboard, Analysis, Settings
 *   analyst -> Dashboard, Analysis only (no Admin Panel)
 * ----------------------------------------------------------
 */

import { createContext, useContext, useState, useCallback } from "react";
import { api, setAuthToken } from "../lib/api";

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [authError, setAuthError] = useState(null);

  const login = useCallback(async (email, password) => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const data = await api.login({ email, password });
      setAuthToken(data.token);
      setToken(data.token);
      setCurrentUser(data.user);
      return { success: true };
    } catch (err) {
      setAuthError(err.message || "Login failed.");
      return { success: false, error: err.message };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async ({ name, email, password }) => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const data = await api.register({ name, email, password });
      setAuthToken(data.token);
      setToken(data.token);
      setCurrentUser(data.user);
      return { success: true };
    } catch (err) {
      setAuthError(err.message || "Registration failed.");
      return { success: false, error: err.message };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loginWithGoogle = useCallback(async (credential) => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const data = await api.googleAuth(credential);
      setAuthToken(data.token);
      setToken(data.token);
      setCurrentUser(data.user);
      return { success: true };
    } catch (err) {
      setAuthError(err.message || "Google login failed.");
      return { success: false, error: err.message };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setAuthToken(null);
    setToken(null);
    setCurrentUser(null);
    setAuthError(null);
  }, []);

  const isAuthenticated = !!token;
  const isAdmin = currentUser?.role === "admin";

  return (
    <AuthContext.Provider
      value={{ isAuthenticated, isAdmin, currentUser, isLoading, authError, login, loginWithGoogle, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
