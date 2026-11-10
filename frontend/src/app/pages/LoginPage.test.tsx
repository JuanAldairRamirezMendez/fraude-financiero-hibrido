import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../auth/AuthContext";
import { LoginPage } from "./LoginPage";

const apiRequestMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/client", () => ({
  ApiError: class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
  apiRequest: apiRequestMock,
}));

describe("LoginPage", () => {
  beforeEach(() => {
    apiRequestMock.mockReset();
    apiRequestMock.mockResolvedValue({ authenticated: false });
  });

  it("envía las credenciales al backend y muestra la sesión", async () => {
    apiRequestMock
      .mockResolvedValueOnce({ authenticated: false })
      .mockResolvedValueOnce({ user: { id: "1", username: "analyst", role: "analyst" } });

    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByLabelText("Usuario")).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText("Usuario"), { target: { value: "analyst" } });
    fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "password" } });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => expect(apiRequestMock).toHaveBeenLastCalledWith("/auth/login", {
      method: "POST",
      body: { username: "analyst", password: "password" },
    }));
  });
});