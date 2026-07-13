import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "./AuthContext";
import { api } from "../lib/api";

vi.mock("../lib/api", () => ({
  api: { login: vi.fn(), register: vi.fn(), googleAuth: vi.fn() },
  setAuthToken: vi.fn(),
}));

function Probe() {
  const { isAuthenticated, currentUser, authError, login, logout } = useAuth();
  return (
    <div>
      <div data-testid="status">{isAuthenticated ? "in" : "out"}</div>
      <div data-testid="user">{currentUser?.email ?? "none"}</div>
      <div data-testid="error">{authError ?? "none"}</div>
      <button onClick={() => login("a@b.com", "pw")}>login</button>
      <button onClick={logout}>logout</button>
    </div>
  );
}

function renderProbe() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>
  );
}

describe("AuthContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts logged out", () => {
    renderProbe();
    expect(screen.getByTestId("status")).toHaveTextContent("out");
  });

  it("becomes authenticated after a successful login", async () => {
    api.login.mockResolvedValue({ token: "jwt-123", user: { email: "a@b.com", role: "analyst" } });
    renderProbe();
    await userEvent.click(screen.getByText("login"));
    expect(await screen.findByTestId("status")).toHaveTextContent("in");
    expect(screen.getByTestId("user")).toHaveTextContent("a@b.com");
  });

  it("surfaces the error message and stays logged out when login fails", async () => {
    api.login.mockRejectedValue(new Error("Invalid email or password"));
    renderProbe();
    await userEvent.click(screen.getByText("login"));
    expect(await screen.findByTestId("error")).toHaveTextContent("Invalid email or password");
    expect(screen.getByTestId("status")).toHaveTextContent("out");
  });

  it("clears state on logout", async () => {
    api.login.mockResolvedValue({ token: "jwt-123", user: { email: "a@b.com", role: "analyst" } });
    renderProbe();
    await userEvent.click(screen.getByText("login"));
    expect(await screen.findByTestId("status")).toHaveTextContent("in");

    await userEvent.click(screen.getByText("logout"));
    expect(screen.getByTestId("status")).toHaveTextContent("out");
    expect(screen.getByTestId("user")).toHaveTextContent("none");
  });
});
