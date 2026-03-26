import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}));

vi.mock("../../api/api", () => ({
  default: {
    get: mockGet,
    post: vi.fn(),
  },
  getErrorMessage: (error, fallback = "Something went wrong.") =>
    error?.response?.data?.error || error?.message || fallback,
}));

import DietitianPortal from "../DietitianPortal";

describe("DietitianPortal", () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it("shows the paywall for free-tier users and routes to upgrade", async () => {
    mockGet.mockRejectedValueOnce({ response: { status: 403 } });

    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/dietitian"]}>
        <Routes>
          <Route path="/dietitian" element={<DietitianPortal />} />
          <Route path="/upgrade/premium" element={<div>Upgrade premium page</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: /unlock the dietitian portal/i })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /upgrade to premium/i }));

    expect(await screen.findByText(/upgrade premium page/i)).toBeInTheDocument();
  });
});
