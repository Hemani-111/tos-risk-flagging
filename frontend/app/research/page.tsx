import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function ResearchPage() {
  return (
    <div className="py-12 sm:py-16">
      <article className="mx-auto max-w-4xl space-y-8 px-4 sm:px-6">
        <header>
          <p className="text-sm font-medium text-muted-foreground">Development research · Phase 4</p>
          <h1 className="mt-2 text-3xl font-semibold">Model comparison</h1>
          <p className="mt-4 max-w-3xl leading-relaxed text-muted-foreground">Experiments use fixed service-aware partitions. Model and feature choices were made with training folds and validation rows; the final test partitions remain locked.</p>
        </header>

        <section className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full min-w-[650px] text-left text-sm">
            <caption className="sr-only">Phase 4 model comparison development results</caption>
            <thead className="bg-secondary/50"><tr>
              <th scope="col" className="p-3 font-semibold">Protocol</th>
              <th scope="col" className="p-3 font-semibold">Candidate</th>
              <th scope="col" className="p-3 font-semibold">CV macro F1</th>
              <th scope="col" className="p-3 font-semibold">Validation macro F1</th>
              <th scope="col" className="p-3 font-semibold">Risky precision / recall</th>
            </tr></thead>
            <tbody className="divide-y divide-border">
              <tr><td className="p-3">Primary unseen-service</td><td className="p-3">Linear SVM, balanced, C=1</td><td className="p-3">0.8316 ± 0.0026</td><td className="p-3">0.8201</td><td className="p-3">0.797 / 0.826</td></tr>
              <tr><td className="p-3">Secondary duplicate-aware</td><td className="p-3">Linear SVM, balanced, C=1</td><td className="p-3">0.8386 ± 0.0021</td><td className="p-3">0.8195</td><td className="p-3">0.787 / 0.845</td></tr>
            </tbody>
          </table>
        </section>

        <section className="space-y-3 text-sm leading-relaxed text-muted-foreground">
          <h2 className="text-xl font-semibold text-foreground">How to read these numbers</h2>
          <p>These are development results on selected conflict-free English excerpts labeled from ToS;DR cases. Primary grouping isolates services; the secondary protocol controls duplicate-aware clause groups and permits service overlap. Macro F1 gives each of the three labels equal weight.</p>
          <p>The two validation estimates describe only these fixed splits. They are not complete-document performance, probability of correctness, legal safety, or expected accuracy on arbitrary uploads. The deployed application still uses the existing RBF SVC; the development Linear SVM has not been promoted.</p>
          <p>Full first-pass family comparisons, fold assignments, feature ablations, per-class counts, resource use, and limitations are in <code>docs/MODEL_EXPERIMENTS_v1.md</code>. Development error and probability analyses are in <code>docs/ERROR_ANALYSIS_v1.md</code>.</p>
        </section>

        <Link href="/about"><Button variant="outline">Read methodology and limitations</Button></Link>
      </article>
    </div>
  );
}
