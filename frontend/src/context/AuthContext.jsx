/**
 * AuthContext — decodes JWT and provides user role/permissions to all components.
 * No extra API call needed: role is embedded in the JWT payload by auth-service.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

// Decode JWT payload without verification (verification is done server-side)
function decodeToken(token) {
  try {
    const payload = token.split('.')[1];
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
    return decoded;
  } catch {
    return null;
  }
}

// Role hierarchy: what each role can access
// _write = create/edit/delete  |  base = read/view only
export const ROLE_PERMISSIONS = {
  admin:           ['billing', 'billing_write', 'inventory', 'inventory_write', 'crm', 'crm_write', 'analytics', 'settings', 'users', 'compliance'],
  manager:         ['billing', 'billing_write', 'inventory', 'inventory_write', 'crm', 'crm_write', 'analytics', 'settings', 'compliance'],
  billing_staff:   ['billing', 'billing_write', 'analytics'],
  inventory_staff: ['inventory', 'analytics'],         // view + adjust stock only, no catalog writes
  crm_staff:       ['crm', 'crm_write', 'analytics'],
  viewer:          ['analytics'],
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const loadUser = useCallback(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setUser(null);
      return;
    }
    const payload = decodeToken(token);
    if (!payload) {
      setUser(null);
      return;
    }
    // Check token expiry
    if (payload.exp && Date.now() / 1000 > payload.exp) {
      localStorage.removeItem('token');
      setUser(null);
      return;
    }
    setUser({
      userId: payload.sub,
      tenantId: payload.tenant_id,
      role: payload.role || 'viewer',
      permissions: ROLE_PERMISSIONS[payload.role] || [],
    });
  }, []);

  useEffect(() => {
    loadUser();
    // Re-load when storage changes (e.g., login in another tab)
    window.addEventListener('storage', loadUser);
    return () => window.removeEventListener('storage', loadUser);
  }, [loadUser]);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setUser(null);
  }, []);

  const hasPermission = useCallback(
    (permission) => {
      if (!user) return false;
      return user.permissions.includes(permission);
    },
    [user]
  );

  return (
    <AuthContext.Provider value={{ user, logout, hasPermission, reload: loadUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
