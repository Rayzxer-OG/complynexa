"use client";

import { useEffect } from "react";

export type ToastVariant = "success" | "error";

interface ToastProps {
  open: boolean;
  message: string;
  variant?: ToastVariant;
  onClose: () => void;
  duration?: number;
}

export function Toast({
  open,
  message,
  variant = "success",
  onClose,
  duration = 4000,
}: ToastProps) {
  useEffect(() => {
    if (!open || !message) return;
    const t = setTimeout(onClose, duration);
    return () => clearTimeout(t);
  }, [open, message, duration, onClose]);

  if (!open) return null;

  const styles =
    variant === "success"
      ? "bg-emerald-800 text-white border-emerald-700"
      : "bg-red-800 text-white border-red-700";

  return (
    <div
      className={`fixed bottom-6 left-1/2 z-[100] -translate-x-1/2 rounded-lg border px-4 py-3 shadow-lg ${styles}`}
      role="status"
      aria-live="polite"
    >
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}
