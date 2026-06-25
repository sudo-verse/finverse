/**
 * Per-page metadata. React 19 hoists <title>/<meta> rendered anywhere in the
 * tree into <head>, so pages can set their own title without react-helmet.
 * Used on the public (crawlable) pages; authenticated pages get their title
 * from the route-title effect in AppLayout.
 */
interface SeoProps {
  title?: string;
  description?: string;
  /** Keep auth-only or utility pages out of the index. */
  noIndex?: boolean;
}

const SUFFIX = "Finverse";
const DEFAULT_TITLE = "Finverse — AI Stock Intelligence for the NSE";

export function Seo({ title, description, noIndex }: SeoProps) {
  const fullTitle = title ? `${title} · ${SUFFIX}` : DEFAULT_TITLE;
  return (
    <>
      <title>{fullTitle}</title>
      {description && <meta name="description" content={description} />}
      {noIndex && <meta name="robots" content="noindex, nofollow" />}
    </>
  );
}
