"use client";

import { Toaster } from "react-hot-toast";
import { ReactNode } from "react";

export default function Providers({ children }: { children: ReactNode }) {
  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            fontSize: "14px",
            borderRadius: "8px",
          },
        }}
      />
      {children}
    </>
  );
}
