import type { UserRole } from "../types";

export const ADMIN_ROLES: readonly UserRole[] = ["data_editor", "admin", "super_admin"];

export function isAdminRole(role: UserRole | null | undefined): boolean {
  return role != null && ADMIN_ROLES.includes(role);
}
