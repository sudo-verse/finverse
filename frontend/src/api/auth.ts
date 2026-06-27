import { apiClient } from "./client";

export interface AuthUser {
  id: number;
  email: string;
  fullName: string | null;
  plan: string;
  createdAt?: string;
}

interface TokenResponse {
  accessToken: string;
  tokenType: string;
  user: AuthUser;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", { email, password });
  return data;
}

export async function register(
  email: string,
  password: string,
  fullName?: string,
): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/register", {
    email,
    password,
    fullName: fullName || null,
  });
  return data;
}

export async function fetchMe(): Promise<AuthUser> {
  const { data } = await apiClient.get<AuthUser>("/auth/me");
  return data;
}

export interface UsageMetric {
  metric: string;
  label: string;
  used: number;
  limit: number | null;
}

export interface Usage {
  plan: string;
  metrics: UsageMetric[];
}

export async function fetchUsage(): Promise<Usage> {
  const { data } = await apiClient.get<Usage>("/usage");
  return data;
}

/** Create a Stripe Checkout session for a plan and return its hosted URL. */
export async function startCheckout(plan: "pro" | "scale" = "pro"): Promise<string> {
  const { data } = await apiClient.post<{ url: string }>("/billing/checkout", { plan });
  return data.url;
}

export interface CashfreeOrder {
  payment_session_id: string;
  order_id: string;
  mode: "sandbox" | "production";
}

/** Create a Cashfree order (INR) and return its hosted-checkout session. */
export async function startCashfreeCheckout(plan: "pro" | "scale" = "pro"): Promise<CashfreeOrder> {
  const { data } = await apiClient.post<CashfreeOrder>("/billing/cashfree/checkout", { plan });
  return data;
}
