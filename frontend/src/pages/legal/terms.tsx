import { Link } from "react-router-dom";
import { LegalPage, Section } from "@/components/legal/legal-page";
import { LEGAL } from "@/lib/legal";

export default function TermsPage() {
  return (
    <LegalPage title="Terms of Service" current="/terms">
      <p>
        These Terms of Service ("Terms") govern your access to and use of {LEGAL.company} (the "Service").
        By creating an account or using the Service, you agree to these Terms. If you do not agree, do not
        use the Service.
      </p>

      <Section heading="1. Eligibility & accounts">
        <p>
          You must be at least 18 years old and capable of forming a binding contract to use {LEGAL.company}.
          You are responsible for safeguarding your account credentials and for all activity under your
          account. Notify us promptly of any unauthorised use.
        </p>
      </Section>

      <Section heading="2. Informational use only">
        <p>
          The Service provides market data, analytics, and AI-generated research for informational and
          educational purposes only. It is not investment advice. See our{" "}
          <Link to="/disclaimer" className="text-primary hover:underline">Disclaimer</Link> for the full
          risk disclosure, which forms part of these Terms.
        </p>
      </Section>

      <Section heading="3. Acceptable use">
        <p>You agree not to:</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>scrape, resell, or redistribute data or content from the Service without permission;</li>
          <li>reverse-engineer, disrupt, or attempt to gain unauthorised access to the Service;</li>
          <li>use the Service for any unlawful purpose or in violation of exchange or regulatory rules;</li>
          <li>misrepresent the Service's output as personalised or registered investment advice.</li>
        </ul>
      </Section>

      <Section heading="4. Third-party data & services">
        <p>
          Market and corporate data is sourced from NSE and other third parties and remains subject to their
          terms and rights. AI features rely on third-party model providers. We are not responsible for the
          availability, accuracy, or actions of third parties.
        </p>
      </Section>

      <Section heading="5. Intellectual property">
        <p>
          The Service, including its software, design, and original content, is owned by {LEGAL.legalEntity}
          and protected by applicable laws. We grant you a limited, non-exclusive, non-transferable licence
          to use the Service for your personal, non-commercial use.
        </p>
      </Section>

      <Section heading="6. Subscriptions & payments">
        <p>
          Paid plans, if offered, are billed as described at checkout. Fees, billing cycles, and any refund
          or cancellation terms will be presented before purchase and are incorporated by reference.
        </p>
      </Section>

      <Section heading="7. Disclaimers & limitation of liability">
        <p>
          The Service is provided "as is" and "as available" without warranties of any kind. To the maximum
          extent permitted by law, {LEGAL.legalEntity} disclaims all warranties and shall not be liable for
          any indirect, incidental, or consequential damages, or for any investment or trading losses
          arising from use of the Service.
        </p>
      </Section>

      <Section heading="8. Termination">
        <p>
          We may suspend or terminate your access at any time for breach of these Terms or to protect the
          Service. You may stop using the Service and delete your account at any time.
        </p>
      </Section>

      <Section heading="9. Changes to these Terms">
        <p>
          We may update these Terms from time to time. Material changes will be notified through the Service
          or by email. Continued use after changes take effect constitutes acceptance.
        </p>
      </Section>

      <Section heading="10. Governing law & contact">
        <p>
          These Terms are governed by the laws of {LEGAL.jurisdiction}. Questions about these Terms can be
          sent to{" "}
          <a href={`mailto:${LEGAL.supportEmail}`} className="text-primary hover:underline">
            {LEGAL.supportEmail}
          </a>.
        </p>
      </Section>
    </LegalPage>
  );
}
