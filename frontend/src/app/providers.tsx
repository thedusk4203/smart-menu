// Gom cac provider toan cuc: xac thuc + thong bao toast.
import type { ReactNode } from "react";
import { Toaster } from "react-hot-toast";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider } from "../context/AuthContext";

export function Providers({ children }: { children: ReactNode }) {
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID?.trim();
  const app = <AuthProvider>{children}</AuthProvider>;

  return (
    <>
      {googleClientId ? <GoogleOAuthProvider clientId={googleClientId}>{app}</GoogleOAuthProvider> : app}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3500,
          style: {
            borderRadius: "0.875rem",
            background: "#1c2b27",
            color: "#fff",
            fontSize: "0.9rem",
          },
          success: { iconTheme: { primary: "#10b981", secondary: "#fff" } },
          error: { iconTheme: { primary: "#ef4444", secondary: "#fff" } },
        }}
      />
    </>
  );
}
