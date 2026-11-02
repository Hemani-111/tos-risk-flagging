import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function AboutPage() {
  return (
    <div className="py-12 sm:py-16">
      <article className="mx-auto max-w-3xl space-y-10 px-4 sm:px-6">
        <header>
          <p className="text-sm font-medium text-muted-foreground">TermsGuard methodology</p>
          <h1 className="mt-2 text-3xl font-semibold">What this screening can and cannot tell you</h1>
          <p className="mt-4 leading-relaxed text-muted-foreground">TermsGuard divides extracted document text into clauses and assigns each analyzable clause one of three labels. It helps you find passages to read more closely; it does not interpret your legal position.</p>
        </header>

        <section className="space-y-3">
          <h2 className="text-xl font-semibold">Labels</h2>
          <dl className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-border p-4"><dt className="font-semibold text-red-700">Risky</dt><dd className="mt-1 text-sm text-muted-foreground">The model associates the clause with adverse examples in its training labels.</dd></div>
            <div className="rounded-lg border border-border p-4"><dt className="font-semibold text-yellow-800">Neutral</dt><dd className="mt-1 text-sm text-muted-foreground">The model associates it with neutral examples.</dd></div>
            <div className="rounded-lg border border-border p-4"><dt className="font-semibold text-green-800">Safe</dt><dd className="mt-1 text-sm text-muted-foreground">The model associates it with examples labeled as protective.</dd></div>
          </dl>
          <p className="text-sm text-muted-foreground">“Safe” is a dataset category. It is not a guarantee, legal opinion, or assessment that the whole document is compliant.</p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-semibold">Model and evidence</h2>
          <p className="text-sm leading-relaxed text-muted-foreground">The current application serves the existing RBF Support Vector Classifier with word unigram/bigram TF-IDF features. Its package version is shown with each result. Development experiments also compared and tuned linear models, but the newer development winner has not been promoted to production.</p>
          <p className="text-sm leading-relaxed text-muted-foreground">The research benchmark uses conflict-reviewed excerpts from ToS;DR and fixed service-aware train, validation, and locked test partitions. The development report records 0.820 macro F1 on primary-protocol validation for the tuned Linear SVM. That is a validation result on selected English excerpts, not a complete-document or future-service accuracy estimate. The locked test partition remains reserved.</p>
          <p className="text-sm leading-relaxed text-muted-foreground">Model scores are not calibrated confidence estimates. No probability or “needs review” threshold is currently used in the app.</p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-semibold">Documents and privacy</h2>
          <p className="text-sm leading-relaxed text-muted-foreground">PDF, DOCX, and TXT files are processed by the configured backend. Scanned or image-only PDFs are unsupported because OCR is not enabled. Uploaded content is held in a temporary server file during analysis and removed afterward; the application does not keep server-side analysis history. Results are stored in session storage for the current browser tab and can be cleared from the results screen.</p>
          <p className="text-sm leading-relaxed text-muted-foreground">The analyzer limits uploads to 10 MB, text to 2,000,000 characters, PDFs to 200 pages, and an analysis to 5,000 clauses. Extraction or segmentation can omit layout and page details; offsets refer to extracted text.</p>
        </section>

        <section className="rounded-lg border border-border bg-secondary/40 p-5">
          <h2 className="text-lg font-semibold">Important</h2>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">This is an educational screening tool, not legal advice. Automated labels can be wrong or miss important material. Read the full terms and consult a qualified legal professional about legal matters.</p>
        </section>

        <Link href="/analyze"><Button>Analyze a document</Button></Link>
      </article>
    </div>
  );
}
