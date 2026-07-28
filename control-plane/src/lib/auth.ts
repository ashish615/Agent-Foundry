"use client";
import { create } from "zustand";

interface JwtPayload {
  sub: string;
  org_id: string;
  scopes: string[];
  exp: number;
}

function decodeJwt(token: string): JwtPayload | null {
  try {
    const part = token.split(".")[1];
    const json = atob(part.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json) as JwtPayload;
  } catch {
    return null;
  }
}

interface AuthState {
  token: string | null;
  userId: string | null;
  orgId: string | null;
  scopes: string[];
  isLoaded: boolean;
  load: () => void;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  token: null,
  userId: null,
  orgId: null,
  scopes: [],
  isLoaded: false,

  load: () => {
    const token = localStorage.getItem("gw_token");
    if (!token) {
      set({ token: null, userId: null, orgId: null, scopes: [], isLoaded: true });
      return;
    }
    const payload = decodeJwt(token);
    if (!payload || payload.exp * 1000 < Date.now()) {
      localStorage.removeItem("gw_token");
      set({ token: null, userId: null, orgId: null, scopes: [], isLoaded: true });
      return;
    }
    set({ token, userId: payload.sub, orgId: payload.org_id, scopes: payload.scopes, isLoaded: true });
  },

  setToken: (token: string) => {
    localStorage.setItem("gw_token", token);
    const payload = decodeJwt(token);
    set({
      token,
      userId: payload?.sub ?? null,
      orgId: payload?.org_id ?? null,
      scopes: payload?.scopes ?? [],
      isLoaded: true,
    });
  },

  logout: () => {
    localStorage.removeItem("gw_token");
    set({ token: null, userId: null, orgId: null, scopes: [], isLoaded: true });
  },
}));
