import Link from "next/link";

function IconPlaceholder({ className }: { className?: string }) {
  return (
    <div
      className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600 ${className ?? ""}`}
      aria-hidden
    >
      <span className="text-lg font-semibold">◇</span>
    </div>
  );
}

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="w-full relative overflow-hidden bg-gradient-to-b from-white to-blue-50/60 px-4 py-20 sm:py-28 opacity-0 animate-fade-in">
        <div className="mx-auto max-w-4xl text-center">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
            AI-powered compliance tracking. Zero missed expiries.
          </h1>
          <p className="mt-6 text-lg text-slate-600 sm:text-xl">
            Complyon uses AWS Textract OCR and AI extraction to automatically detect document expiries, categorize compliance records, and send reminders before deadlines.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/register"
              className="rounded-lg bg-blue-600 px-6 py-3.5 text-sm font-semibold text-white shadow-md transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Get Started Free
            </Link>
            <Link
              href="/login"
              className="rounded-lg border border-slate-300 bg-white px-6 py-3.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2"
            >
              Login
            </Link>
          </div>
          <div className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-4 border-t border-slate-200/80 pt-10">
            <span className="flex items-center gap-2 text-sm text-slate-600">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              AI-powered document intelligence
            </span>
            <span className="flex items-center gap-2 text-sm text-slate-600">
              <span className="h-2 w-2 rounded-full bg-blue-500" />
              Powered by AWS Textract OCR
            </span>
            <span className="flex items-center gap-2 text-sm text-slate-600">
              <span className="h-2 w-2 rounded-full bg-slate-400" />
              Secure cloud infrastructure
            </span>
          </div>
        </div>
      </section>

      {/* Technology Trust */}
      <section className="border-t border-slate-200 bg-white px-4 py-20 opacity-0 animate-fade-in [animation-delay:80ms]">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-center text-2xl font-semibold text-slate-900 sm:text-3xl">
            Powered by enterprise-grade AI and AWS infrastructure
          </h2>
          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-6 shadow-sm transition hover:shadow-md">
              <IconPlaceholder />
              <h3 className="mt-4 font-semibold text-slate-900">AWS Textract OCR</h3>
              <p className="mt-2 text-sm text-slate-600">
                Extract text accurately from multi-page compliance documents.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-6 shadow-sm transition hover:shadow-md">
              <IconPlaceholder />
              <h3 className="mt-4 font-semibold text-slate-900">AI Expiry Detection</h3>
              <p className="mt-2 text-sm text-slate-600">
                Automatically detect expiry dates, document names, and compliance categories.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-6 shadow-sm transition hover:shadow-md">
              <IconPlaceholder />
              <h3 className="mt-4 font-semibold text-slate-900">Intelligent Reminder Engine</h3>
              <p className="mt-2 text-sm text-slate-600">
                Smart reminders prevent compliance failures and penalties.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-6 shadow-sm transition hover:shadow-md">
              <IconPlaceholder />
              <h3 className="mt-4 font-semibold text-slate-900">Secure Cloud Storage</h3>
              <p className="mt-2 text-sm text-slate-600">
                Documents securely stored with enterprise-grade infrastructure.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-slate-200 bg-slate-50/40 px-4 py-20 opacity-0 animate-fade-in [animation-delay:160ms]">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-center text-2xl font-semibold text-slate-900 sm:text-3xl">
            Everything you need to stay compliant
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-center text-slate-600">
            AI-powered automation and visibility across all your compliance documents.
          </p>
          <div className="mt-14 grid gap-6 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md">
              <h3 className="font-semibold text-slate-900">AI document processing</h3>
              <p className="mt-2 text-sm text-slate-600">
                Automatically extract compliance data using AI.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md">
              <h3 className="font-semibold text-slate-900">Expiry tracking dashboard</h3>
              <p className="mt-2 text-sm text-slate-600">
                See active, expiring, and expired documents instantly.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md">
              <h3 className="font-semibold text-slate-900">Automated reminders</h3>
              <p className="mt-2 text-sm text-slate-600">
                Email alerts before compliance deadlines.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md">
              <h3 className="font-semibold text-slate-900">Centralized compliance hub</h3>
              <p className="mt-2 text-sm text-slate-600">
                Manage all compliance documents in one place.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-slate-200 bg-white px-4 py-20 opacity-0 animate-fade-in [animation-delay:240ms]">
        <div className="mx-auto max-w-3xl">
          <h2 className="text-center text-2xl font-semibold text-slate-900 sm:text-3xl">
            How Complyon works
          </h2>
          <ol className="mt-14 flex flex-col gap-10 sm:gap-14">
            <li className="flex gap-5">
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-blue-600 text-base font-semibold text-white">
                1
              </span>
              <div>
                <h3 className="font-semibold text-slate-900">Upload compliance documents</h3>
                <p className="mt-2 text-slate-600">
                  Upload PDFs like licenses, insurance policies, and certificates.
                </p>
              </div>
            </li>
            <li className="flex gap-5">
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-blue-600 text-base font-semibold text-white">
                2
              </span>
              <div>
                <h3 className="font-semibold text-slate-900">AI processes documents</h3>
                <p className="mt-2 text-slate-600">
                  AWS Textract OCR extracts text. AI detects expiry and compliance data.
                </p>
              </div>
            </li>
            <li className="flex gap-5">
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-blue-600 text-base font-semibold text-white">
                3
              </span>
              <div>
                <h3 className="font-semibold text-slate-900">Track and get reminders</h3>
                <p className="mt-2 text-slate-600">
                  Monitor compliance status and receive automated alerts.
                </p>
              </div>
            </li>
          </ol>
        </div>
      </section>

      {/* Problem / Value */}
      <section className="border-t border-slate-200 bg-slate-50/40 px-4 py-20 opacity-0 animate-fade-in [animation-delay:320ms]">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-2xl font-semibold text-slate-900 sm:text-3xl">
            Manual compliance tracking is risky. Complyon automates it.
          </h2>
          <ul className="mt-12 flex flex-col gap-4 text-left sm:mx-auto sm:max-w-md">
            <li className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <span className="h-2 w-2 shrink-0 rounded-full bg-blue-600" />
              Avoid compliance failures and penalties
            </li>
            <li className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <span className="h-2 w-2 shrink-0 rounded-full bg-blue-600" />
              Never miss renewal deadlines
            </li>
            <li className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <span className="h-2 w-2 shrink-0 rounded-full bg-blue-600" />
              Eliminate manual tracking errors
            </li>
            <li className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <span className="h-2 w-2 shrink-0 rounded-full bg-blue-600" />
              Maintain audit readiness
            </li>
            <li className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <span className="h-2 w-2 shrink-0 rounded-full bg-blue-600" />
              Save time with automation
            </li>
          </ul>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-gradient-to-br from-slate-800 via-blue-900 to-slate-900 px-4 py-20 text-white opacity-0 animate-fade-in [animation-delay:400ms]">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-2xl font-semibold sm:text-3xl">
            Start using AI to manage compliance today
          </h2>
          <p className="mt-4 text-blue-100/90">
            Join Complyon and automate compliance tracking with AI and AWS-powered OCR.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/register"
              className="rounded-lg bg-white px-6 py-3.5 text-sm font-semibold text-slate-900 shadow-md transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-slate-900"
            >
              Get Started Free
            </Link>
            <Link
              href="/login"
              className="rounded-lg border border-blue-400/50 bg-transparent px-6 py-3.5 text-sm font-medium text-white transition hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:ring-offset-2 focus:ring-offset-slate-900"
            >
              Login
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full border-t border-slate-200 bg-slate-900 px-4 py-12 text-slate-300 opacity-0 animate-fade-in [animation-delay:480ms]">
        <div className="mx-auto max-w-4xl">
          <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
            <div>
              <p className="font-bold text-white">Complyon</p>
              <p className="mt-0.5 text-sm">AI-powered compliance tracking</p>
              <p className="mt-2 text-xs text-slate-400">Powered by AWS Textract and AI</p>
            </div>
            <nav className="flex gap-6">
              <Link href="/login" className="text-sm hover:text-white">
                Login
              </Link>
              <Link href="/register" className="text-sm hover:text-white">
                Register
              </Link>
            </nav>
          </div>
          <p className="mt-8 border-t border-slate-700 pt-8 text-center text-xs text-slate-500">
            © 2026 Complyon. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
