import { startCashfreeCheckout } from "@/api/auth";

const SDK_URL = "https://sdk.cashfree.com/js/v3/cashfree.js";

declare global {
  interface Window {
    // The v3 SDK exposes a global Cashfree factory.
    Cashfree?: (opts: { mode: "sandbox" | "production" }) => {
      checkout: (opts: { paymentSessionId: string; redirectTarget?: string }) => Promise<unknown>;
    };
  }
}

let sdkPromise: Promise<void> | null = null;

function loadSdk(): Promise<void> {
  if (sdkPromise) return sdkPromise;
  sdkPromise = new Promise((resolve, reject) => {
    if (window.Cashfree) return resolve();
    const s = document.createElement("script");
    s.src = SDK_URL;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => {
      sdkPromise = null;
      reject(new Error("Failed to load the Cashfree SDK."));
    };
    document.head.appendChild(s);
  });
  return sdkPromise;
}

/**
 * Start a Cashfree upgrade: create the order on the backend, then open Cashfree's
 * hosted checkout in the current tab. On payment Cashfree returns to
 * /settings?billing=success and the webhook activates the plan.
 */
export async function cashfreeUpgrade(plan: "pro" | "scale"): Promise<void> {
  const order = await startCashfreeCheckout(plan);
  await loadSdk();
  if (!window.Cashfree) throw new Error("Cashfree SDK unavailable.");
  const cashfree = window.Cashfree({ mode: order.mode });
  await cashfree.checkout({ paymentSessionId: order.payment_session_id, redirectTarget: "_self" });
}
