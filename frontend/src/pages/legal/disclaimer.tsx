import { LegalPage, Section } from "@/components/legal/legal-page";
import { LEGAL } from "@/lib/legal";

export default function DisclaimerPage() {
  return (
    <LegalPage title="Disclaimer & Risk Disclosure" current="/disclaimer">
      <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-zinc-200">
        <strong>{LEGAL.company} is not a SEBI-registered investment adviser or research analyst.</strong>{" "}
        Everything on this platform is provided for informational and educational purposes only and must
        not be construed as investment advice, a recommendation, or a solicitation to buy or sell any
        security.
      </p>

      <Section heading="Not investment advice">
        <p>
          Signals, scores, "fair value" estimates, "undervalued/overvalued" verdicts, earnings-momentum
          labels, screeners, and any other output are algorithmic, generalised, and not tailored to your
          financial situation, objectives, or risk tolerance. They are not a substitute for advice from a
          SEBI-registered investment adviser or your own independent judgement.
        </p>
      </Section>

      <Section heading="Market risk">
        <p>
          Investments in securities are subject to market and other risks. The value of investments can go
          down as well as up, and you may lose some or all of your capital. Past performance is not
          indicative of future results. No representation is made that any account will or is likely to
          achieve profits or losses similar to those discussed.
        </p>
      </Section>

      <Section heading="Data accuracy & sources">
        <p>
          Market and corporate data is sourced from the National Stock Exchange of India (NSE), company
          filings, and other third parties. It may be delayed, incomplete, or inaccurate. We do not warrant
          the accuracy, completeness, or timeliness of any data, and AI-generated research may contain
          errors or "hallucinations." Always verify against official exchange and company sources before
          acting.
        </p>
      </Section>

      <Section heading="Do your own research">
        <p>
          You are solely responsible for your investment decisions. Conduct your own due diligence and
          consult a qualified, SEBI-registered financial adviser before making any investment. Never invest
          money you cannot afford to lose.
        </p>
      </Section>

      <Section heading="No liability">
        <p>
          To the maximum extent permitted by law, {LEGAL.legalEntity} and its team accept no liability for
          any loss or damage — including trading or investment losses — arising from reliance on any
          information, signal, or analysis provided by the platform.
        </p>
      </Section>

      <Section heading="No fiduciary relationship">
        <p>
          Use of {LEGAL.company} does not create any advisory, fiduciary, or brokerage relationship between
          you and us. We do not execute trades, hold client funds, or manage portfolios on your behalf.
        </p>
      </Section>
    </LegalPage>
  );
}
