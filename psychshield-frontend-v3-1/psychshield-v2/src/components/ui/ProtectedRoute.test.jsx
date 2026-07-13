import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import * as AuthContext from "../../context/AuthContext";

function renderProtected({ adminOnly = false } = {}) {
  return render(
    <MemoryRouter initialEntries={["/analysis"]}>
      <Routes>
        <Route path="/login" element={<div>Login page</div>} />
        <Route path="/unauthorized" element={<div>Unauthorized page</div>} />
        <Route
          path="/analysis"
          element={
            <ProtectedRoute adminOnly={adminOnly}>
              <div>Protected content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>
  );
}

describe("ProtectedRoute", () => {
  it("redirects to /login when not authenticated", () => {
    vi.spyOn(AuthContext, "useAuth").mockReturnValue({ isAuthenticated: false, isAdmin: false });
    renderProtected();
    expect(screen.getByText("Login page")).toBeInTheDocument();
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });

  it("renders children when authenticated", () => {
    vi.spyOn(AuthContext, "useAuth").mockReturnValue({ isAuthenticated: true, isAdmin: false });
    renderProtected();
    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });

  it("redirects to /unauthorized when authenticated but not admin on an admin-only route", () => {
    vi.spyOn(AuthContext, "useAuth").mockReturnValue({ isAuthenticated: true, isAdmin: false });
    renderProtected({ adminOnly: true });
    expect(screen.getByText("Unauthorized page")).toBeInTheDocument();
  });

  it("renders children for an admin on an admin-only route", () => {
    vi.spyOn(AuthContext, "useAuth").mockReturnValue({ isAuthenticated: true, isAdmin: true });
    renderProtected({ adminOnly: true });
    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });
});
