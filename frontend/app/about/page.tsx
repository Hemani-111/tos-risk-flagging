import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { FiHelpCircle } from "react-icons/fi";

const labels = [
  {
    label: "Risky",
    detail: "The clause resembles language the training data associated with adverse outcomes. Read it closely.",
    color: "#7a2e28",
  },
  {
    label: "Neutral",
    detail: "The clause does not carry a clear protective or adverse signal in the training labels.",
    color: "#7a5d1c",
  },
  {
    label: "Safe",
    detail: "The clause resembles language the training data associated with protective terms.",
    color: "#3d6a4e",
  },
];

export default function HowItWorksPage() {
  return (
    <div className="py-12 sm:py-16">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <header className="mb-10">
          <p className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <FiHelpCircle className="h-4 w-4" aria-hidden="true" />
            How it works
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            What this preview shows
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
            TermsGuard is an interactive UI preview. It uses illustrative sample clauses to demonstrate
            clause-by-clause review — it is not connected to a machine-learning model or a FastAPI
            backend, and it does not upload or analyze your documents.
          </p>
        </header>

        <section className="mb-10 rounded-xl border border-border bg-card p-6 sm:p-8 shadow-sm">
          <h2 className="text-xl font-semibold text-foreground mb-4">How to use it</h2>
          <ol className="space-y-4">
            <li className="flex gap-3">
              <span className="flex shrink-0 h-8 w-8 items-center justify-center rounded-lg bg-secondary text-xs font-semibold text-muted-foreground">
                01
              </span>
              <div>
                <h3 className="font-semibold text-foreground">Add a policy</h3>
                <p className="mt-1 text-sm text-muted-foreground">Upload a PDF, DOCX, or TXT file, or paste policy text on the Analyze page.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="flex shrink-0 h-8 w-8 items-center justify-center rounded-lg bg-secondary text-xs font-semibold text-muted-foreground">
                02
              </span>
              <div>
                <h3 className="font-semibold text-foreground">See clause predictions</h3>
                <p className="mt-1 text-sm text-muted-foreground">Browse clauses labeled Safe, Neutral, or Risky, then narrow the list with search and filters.</p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="flex shrink-0 h-8 w-8 items-center justify-center rounded-lg bg-secondary text-xs font-semibold text-muted-foreground">
                03
              </span>
              <div>
                <h3 className="font-semibold text-foreground">Read in context</h3>
                <p className="mt-1 text-sm text-muted-foreground">Select a clause to jump to its source in the document and inspect neighboring clauses.</p>
              </div>
            </li>
          </ol>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-foreground mb-4">Label categories</h2>
          <p className="mb-4 text-sm text-muted-foreground">
            Each sample clause carries one of three labels. These are screening categories, not legal
            conclusions.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            {labels.map(({ label, detail, color }) => (
              <div key={label} className="rounded-lg border border-border p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="inline-flex items-center rounded-full" style={{ width: 8, height: 8, backgroundColor: color }} aria-hidden="true" />
                  <span className="font-semibold text-foreground">{label}</span>
                </div>
                <p className="text-sm leading-relaxed text-muted-foreground" style={{ color: color }}>{detail}</p>
              </div>
            ))}
          </div>
          <p className="mt-5 text-sm text-muted-foreground">
            “Safe” is a sample category. It is not a guarantee, legal opinion, or an assessment that
            the whole document is compliant.
          </p>
        </section>

        <section className="rounded-xl border border-border bg-secondary/40 p-6 sm:p-8">
          <h2 className="text-lg font-semibold text-foreground mb-2">Important limitations</h2>
          <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-5">
            <li>The sample clauses are illustrative and do not come from a trained model.</li>
            <li>No document is uploaded, stored, or analyzed by this preview.</li>
            <li>Labels are screening predictions — they can be wrong or miss important context.</li>
            <li>This is educational screening, not legal advice. Consult a qualified professional for legal matters.</li>
          </ul>
        </section>

        <div className="mt-10 flex justify-end">
          <Link href="/">
            <Button>Start a sample review</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
