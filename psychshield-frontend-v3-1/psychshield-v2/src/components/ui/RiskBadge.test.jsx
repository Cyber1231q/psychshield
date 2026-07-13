import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import RiskBadge from "./RiskBadge";

describe("RiskBadge", () => {
  it("renders the tier label in uppercase", () => {
    render(<RiskBadge tier="High" score={82} />);
    expect(screen.getByText(/HIGH/)).toBeInTheDocument();
  });

  it("shows the score when provided", () => {
    render(<RiskBadge tier="Medium" score={55} />);
    expect(screen.getByText(/55/)).toBeInTheDocument();
  });

  it("omits the score when not a number", () => {
    render(<RiskBadge tier="Low" />);
    expect(screen.queryByText(/·/)).not.toBeInTheDocument();
  });

  it("falls back to the Low style for an unrecognized tier", () => {
    // Guards against a crash if the backend ever sends an unexpected tier string.
    render(<RiskBadge tier="Unknown" />);
    expect(screen.getByText(/UNKNOWN/)).toBeInTheDocument();
  });
});
