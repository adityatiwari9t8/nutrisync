import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { mockPost, mockGetStoredUser, mockStoreAuth } = vi.hoisted(() => ({
  mockPost: vi.fn(),
  mockGetStoredUser: vi.fn(),
  mockStoreAuth: vi.fn(),
}));

vi.mock("../../api/api", () => ({
  default: {
    post: mockPost,
  },
  getErrorMessage: (error, fallback = "Something went wrong.") =>
    error?.response?.data?.error || error?.message || fallback,
  getStoredUser: mockGetStoredUser,
  storeAuth: mockStoreAuth,
}));

import Register from "../Register";

describe("Register", () => {
  beforeEach(() => {
    mockPost.mockReset();
    mockGetStoredUser.mockReset();
    mockStoreAuth.mockReset();
    mockGetStoredUser.mockReturnValue(null);
  });

  it("creates the account as free and sends premium-selected users into the upgrade flow", async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        access_token: "test-token",
        user: {
          id: 11,
          username: "Riya",
          email: "riya@example.com",
          is_premium: false,
          created_at: "2026-03-27T00:00:00Z",
        },
      },
    });

    const onAuthSuccess = vi.fn();
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/register"]}>
        <Routes>
          <Route path="/register" element={<Register onAuthSuccess={onAuthSuccess} />} />
          <Route path="/upgrade/premium" element={<div>Upgrade premium page</div>} />
        </Routes>
      </MemoryRouter>,
    );

    await user.type(screen.getByPlaceholderText(/username/i), "Riya");
    await user.type(screen.getByPlaceholderText(/email address/i), "riya@example.com");
    await user.type(screen.getByPlaceholderText(/password/i), "securepass");
    await user.click(screen.getByRole("checkbox", { name: /include premium insights/i }));
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith("/auth/register", {
        username: "Riya",
        email: "riya@example.com",
        password: "securepass",
        is_premium: false,
      });
    });

    expect(mockStoreAuth).toHaveBeenCalledWith({
      access_token: "test-token",
      user: {
        id: 11,
        username: "Riya",
        email: "riya@example.com",
        is_premium: false,
        created_at: "2026-03-27T00:00:00Z",
      },
    });
    expect(onAuthSuccess).toHaveBeenCalled();
    expect(await screen.findByText(/upgrade premium page/i)).toBeInTheDocument();
  });
});
