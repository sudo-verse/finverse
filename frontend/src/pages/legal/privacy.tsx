import { LegalPage, Section } from "@/components/legal/legal-page";
import { LEGAL } from "@/lib/legal";

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy" current="/privacy">
      <p>
        This Privacy Policy explains how {LEGAL.legalEntity} ("we") collects, uses, and protects your
        personal data when you use {LEGAL.company}, in line with India's Digital Personal Data Protection
        Act, 2023 (DPDP Act).
      </p>

      <Section heading="Data we collect">
        <ul className="list-disc space-y-1 pl-5">
          <li><strong>Account data:</strong> your name and email address when you register.</li>
          <li><strong>Usage data:</strong> watchlists, portfolio holdings you add, preferences, and alert settings.</li>
          <li><strong>Technical data:</strong> log data such as IP address, device/browser type, and request timestamps, used for security and reliability.</li>
        </ul>
      </Section>

      <Section heading="How we use your data">
        <ul className="list-disc space-y-1 pl-5">
          <li>to provide, secure, and improve the Service;</li>
          <li>to authenticate you and maintain your account;</li>
          <li>to send service and (with consent) alert notifications;</li>
          <li>to comply with legal obligations and prevent abuse.</li>
        </ul>
        <p>
          We process your data on the basis of your consent and to perform our contract with you. We do not
          sell your personal data.
        </p>
      </Section>

      <Section heading="Sharing & processors">
        <p>
          We share data only with service providers that help us run the Service — for example cloud hosting,
          database, and email/AI providers — under appropriate safeguards. Market data is obtained from NSE
          and other sources and is not personal to you.
        </p>
      </Section>

      <Section heading="Data retention">
        <p>
          We retain personal data for as long as your account is active or as needed to provide the Service
          and meet legal obligations. You can request deletion at any time (see your rights below).
        </p>
      </Section>

      <Section heading="Your rights">
        <p>Under the DPDP Act you have the right to:</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>access and obtain a copy of your personal data;</li>
          <li>correct or update inaccurate data;</li>
          <li>request erasure of your data ("right to be forgotten");</li>
          <li>withdraw consent and grieve through our grievance officer.</li>
        </ul>
        <p>
          To exercise these rights, contact us at{" "}
          <a href={`mailto:${LEGAL.grievanceEmail}`} className="text-primary hover:underline">
            {LEGAL.grievanceEmail}
          </a>.
        </p>
      </Section>

      <Section heading="Security">
        <p>
          We use industry-standard measures — encrypted transport (HTTPS), hashed passwords, and access
          controls — to protect your data. No method of transmission or storage is completely secure, and we
          cannot guarantee absolute security.
        </p>
      </Section>

      <Section heading="Cookies">
        <p>
          We use essential cookies/local storage to keep you signed in and remember preferences. If we
          introduce analytics, we will request consent and update this policy accordingly.
        </p>
      </Section>

      <Section heading="Children">
        <p>The Service is not directed to anyone under 18, and we do not knowingly collect their data.</p>
      </Section>

      <Section heading="Contact & grievance officer">
        <p>
          For any privacy questions or to reach our grievance officer, email{" "}
          <a href={`mailto:${LEGAL.grievanceEmail}`} className="text-primary hover:underline">
            {LEGAL.grievanceEmail}
          </a>. We will respond within the timelines required by law.
        </p>
      </Section>
    </LegalPage>
  );
}
