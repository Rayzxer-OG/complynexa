const TOKEN_KEY = "access_token";
const UNIT_ID_KEY = "unit_id";
const ORGANIZATION_ID_KEY = "organization_id";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export function getUnitId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(UNIT_ID_KEY);
}

export function setUnitId(unitId: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(UNIT_ID_KEY, unitId);
}

export function getOrganizationId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ORGANIZATION_ID_KEY);
}

export function setOrganizationId(organizationId: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ORGANIZATION_ID_KEY, organizationId);
}
