import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import GmailConnect from "./GmailConnect";
import { api, API_BASE_URL } from "../../lib/api";

vi.mock("../../lib/api", () => ({
  api: { gmailStatus: vi.fn(), gmailConnect: vi.fn(), gmailDisconnect: vi.fn() },
  API_BASE_URL: "http://localhost:8000",
}));

describe("GmailConnect", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows 'Not connected' and a Connect button when Gmail isn't linked", async () => {
    api.gmailStatus.mockResolvedValue({ connected: false });
    render(<GmailConnect />);
    expect(await screen.findByText("Not connected")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /connect gmail/i })).toBeInTheDocument();
  });

  it("shows 'Connected' and a Disconnect button when Gmail is linked", async () => {
    api.gmailStatus.mockResolvedValue({ connected: true });
    render(<GmailConnect />);
    expect(await screen.findByText("Connected")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /disconnect gmail/i })).toBeInTheDocument();
  });

  it("opens a popup to the auth_url when Connect Gmail is clicked", async () => {
    api.gmailStatus.mockResolvedValue({ connected: false });
    api.gmailConnect.mockResolvedValue({ auth_url: "https://accounts.google.com/o/oauth2/auth?x=1" });
    const openSpy = vi.spyOn(window, "open").mockReturnValue({ closed: false });

    render(<GmailConnect />);
    await userEvent.click(await screen.findByRole("button", { name: /connect gmail/i }));

    await waitFor(() => expect(openSpy).toHaveBeenCalledWith(
      "https://accounts.google.com/o/oauth2/auth?x=1",
      "psychshield-gmail-oauth",
      expect.any(String)
    ));
  });

  it("shows an error when the popup is blocked", async () => {
    api.gmailStatus.mockResolvedValue({ connected: false });
    api.gmailConnect.mockResolvedValue({ auth_url: "https://accounts.google.com/o/oauth2/auth" });
    vi.spyOn(window, "open").mockReturnValue(null); // simulates a blocked popup

    render(<GmailConnect />);
    await userEvent.click(await screen.findByRole("button", { name: /connect gmail/i }));

    expect(await screen.findByText(/blocked the gmail sign-in popup/i)).toBeInTheDocument();
  });

  // Regression test: the popup's callback page is served by the BACKEND
  // (API_BASE_URL), not this frontend's own origin — a real bug this
  // session had the listener checking against window.location.origin
  // instead, which silently dropped every legitimate success message.
  it("re-checks status after receiving a postMessage from the backend's origin", async () => {
    api.gmailStatus.mockResolvedValueOnce({ connected: false }).mockResolvedValueOnce({ connected: true });
    render(<GmailConnect />);
    await screen.findByText("Not connected");

    window.dispatchEvent(
      new MessageEvent("message", {
        origin: new URL(API_BASE_URL).origin,
        data: { source: "psychshield-gmail-oauth", status: "connected" },
      })
    );

    await waitFor(() => expect(api.gmailStatus).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Connected")).toBeInTheDocument();
  });

  it("ignores a postMessage from an untrusted origin", async () => {
    api.gmailStatus.mockResolvedValue({ connected: false });
    render(<GmailConnect />);
    await screen.findByText("Not connected");

    window.dispatchEvent(
      new MessageEvent("message", {
        origin: "https://evil.example.com",
        data: { source: "psychshield-gmail-oauth", status: "connected" },
      })
    );

    // Only the initial mount call — the forged message must not trigger a re-check.
    await new Promise((r) => setTimeout(r, 10));
    expect(api.gmailStatus).toHaveBeenCalledTimes(1);
  });
});
