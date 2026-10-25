import Link from "next/link";
export default function NotFound() {
  return (
    <div className="page-intro">
      <p className="eyebrow">Nothing in this burrow</p>
      <h1>That page isn’t available.</h1>
      <p className="lede">
        It may be awaiting editorial approval, or the link may have changed.
      </p>
      <Link className="button" href="/">
        Back to home →
      </Link>
    </div>
  );
}
