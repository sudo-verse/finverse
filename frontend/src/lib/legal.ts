/**
 * Central legal/brand metadata used across the footer and legal pages.
 *
 * NOTE: The Terms, Privacy and Disclaimer copy is a sensible, India-aware
 * starting template — it is NOT a substitute for review by qualified legal
 * counsel before a commercial launch. Confirm the entity name, jurisdiction,
 * grievance-officer details and SEBI positioning with a lawyer.
 */
export const LEGAL = {
  company: "Finverse",
  legalEntity: "Finverse", // TODO: replace with the registered legal entity name
  supportEmail: "support@finverse.app", // TODO: confirm a real, monitored inbox
  grievanceEmail: "grievance@finverse.app", // TODO: DPDP grievance officer contact
  jurisdiction: "India",
  lastUpdated: "26 June 2026",
} as const;

export const LEGAL_LINKS = [
  { to: "/disclaimer", label: "Disclaimer" },
  { to: "/terms", label: "Terms" },
  { to: "/privacy", label: "Privacy" },
] as const;

/** Short, persistent not-investment-advice line shown in the footer. */
export const SHORT_DISCLAIMER =
  "Finverse provides data and analysis for informational and educational purposes only. " +
  "It is not a SEBI-registered investment adviser or research analyst, and nothing here is " +
  "investment advice. Market data may be delayed or inaccurate. Source: NSE. " +
  "Investments are subject to market risk — do your own research and consult a registered adviser.";
