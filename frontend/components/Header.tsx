import Link from "next/link";

export function Header() {
  return (
    <header className="border-b border-line bg-card/80">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <Link href="/" className="font-serif text-xl tracking-tight">
          Multi-Agent Article Studio
        </Link>
        <nav className="flex gap-4 text-sm">
          <Link href="/" className="hover:text-teal">
            記事一覧
          </Link>
          <Link href="/articles/new" className="hover:text-teal">
            新規作成
          </Link>
        </nav>
      </div>
    </header>
  );
}
