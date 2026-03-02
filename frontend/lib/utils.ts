export type DocumentStatus = "expired" | "expiring_soon" | "active";

export function getStatus(expiryDate: string | null): DocumentStatus | null {
  if (!expiryDate) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const expiry = new Date(expiryDate);
  expiry.setHours(0, 0, 0, 0);
  if (expiry < today) return "expired";
  const daysUntil = Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  if (daysUntil <= 30) return "expiring_soon";
  return "active";
}

/** Format ISO date (YYYY-MM-DD) for display as DD/MM/YYYY. Backend continues to store ISO. */
export function formatDateDDMMYYYY(dateStr: string | null): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return "—";
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
}

/** Format date for UI display (DD/MM/YYYY). Use for expiry and other dates. */
export function formatDate(dateStr: string | null): string {
  return formatDateDDMMYYYY(dateStr);
}
