import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { ArrowRight, FileText, SearchCheck, ShieldAlert, Upload } from "lucide-react";

const steps = [
  { number: "01", title: "Add a policy", detail: "Upload a PDF, DOCX, or TXT file, or paste policy text." },
  { number: "02", title: "Review clauses", detail: "See extracted clauses with a model-assigned label." },
  { number: "03", title: "Read in context", detail: "Search, filter, and inspect nearby clauses before drawing conclusions." },
];

const features = [
  { icon: FileText, title: "Clause-by-clause view", detail: "Keep the original wording visible while reviewing each result." },
  { icon: SearchCheck, title: "Useful review tools", detail: "Find text, filter by label, and inspect adjacent clauses." },
  { icon: ShieldAlert, title: "Clear limitations", detail: "See what the labels mean and where the model can be wrong." },
];

export default function HomePage() {
  return (
    <div>
      <section className="border-b border-border bg-gradient-to-b from-secondary/70 to-background">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24 lg:py-28">
          <div className="mx-auto max-w-3xl text-center">
            <span className="inline-flex items-center rounded-full border border-border bg-background px-3 py-1 text-xs font-medium text-muted-foreground">A clearer first pass through policy text</span>
            <h1 className="mt-6 text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-6xl">Make the fine print easier to review.</h1>
            <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">TermsGuard organizes extracted clauses and flags passages that may deserve a closer read.</p>
            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              <Link href="/analyze"><Button size="lg" className="w-full sm:w-auto"><Upload className="mr-2 h-4 w-4" />Analyze a document</Button></Link>
              <Link href="#how-it-works"><Button variant="outline" size="lg" className="w-full sm:w-auto">How it works<ArrowRight className="ml-2 h-4 w-4" /></Button></Link>
            </div>
            <p className="mt-5 text-xs text-muted-foreground">PDF, DOCX, or TXT · Up to 10 MB · English-language model</p>
          </div>
        </div>
      </section>

      <section id="how-it-works" className="mx-auto max-w-6xl scroll-mt-24 px-4 py-16 sm:px-6 sm:py-20">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold text-muted-foreground">Simple workflow</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">From policy file to focused review</h2>
        </div>
        <ol className="mt-8 grid gap-4 md:grid-cols-3">
          {steps.map((step) => <li key={step.number} className="rounded-xl border border-border bg-card p-6">
            <span className="text-sm font-semibold tabular-nums text-muted-foreground">{step.number}</span>
            <h3 className="mt-5 text-base font-semibold">{step.title}</h3>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{step.detail}</p>
          </li>)}
        </ol>
      </section>

      <section className="border-y border-border bg-secondary/30">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
          <div className="grid gap-8 md:grid-cols-[0.8fr_1.2fr] md:items-start">
            <div>
              <p className="text-sm font-semibold text-muted-foreground">Designed for review</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">Keep the wording in view.</h2>
              <p className="mt-4 text-sm leading-6 text-muted-foreground">Use the results page to browse extracted clauses, narrow the list, and keep nearby text close while you read.</p>
              <Link href="/about" className="mt-5 inline-flex items-center text-sm font-medium hover:underline">Learn about the methodology<ArrowRight className="ml-2 h-4 w-4" /></Link>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {features.map(({ icon: Icon, title, detail }) => <article key={title} className="rounded-xl border border-border bg-background p-5">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary"><Icon className="h-4 w-4" aria-hidden="true" /></span>
                <h3 className="mt-4 text-sm font-semibold">{title}</h3>
                <p className="mt-2 text-sm leading-5 text-muted-foreground">{detail}</p>
              </article>)}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14 sm:px-6 sm:py-16">
        <div className="flex flex-col gap-5 rounded-xl border border-border bg-card p-6 sm:flex-row sm:items-center sm:justify-between sm:p-8">
          <div className="max-w-2xl">
            <h2 className="text-xl font-semibold tracking-tight">Ready to review a policy?</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">Start with a document you are permitted to share. Your results remain in this browser tab.</p>
          </div>
          <Link href="/analyze"><Button><Upload className="mr-2 h-4 w-4" />Get started</Button></Link>
        </div>
        <p className="mt-6 text-center text-xs leading-5 text-muted-foreground">TermsGuard is an educational screening tool, not legal advice. Model labels can be wrong or miss important context.</p>
      </section>
    </div>
  );
}
