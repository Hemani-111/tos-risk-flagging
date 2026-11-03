import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { COMPARISON_ROWS, PRODUCTION_MODEL } from "@/lib/comparisonData";

export default function ResearchPage() {
  return (
    <div className="py-12 sm:py-16">
      <article className="mx-auto max-w-7xl space-y-8 px-4 sm:px-6">
        <header>
          <p className="text-sm font-medium text-muted-foreground">Model comparison</p>
          <h1 className="mt-2 text-3xl font-semibold">Standard classifier comparison</h1>
          <p className="mt-4 max-w-4xl leading-relaxed text-muted-foreground">
            All eight methods were trained and tuned on the same prepared development data with
            fixed group-respecting splits. Macro F1 is the selection metric; Risky precision and
            recall are reported alongside. The locked test partition was not used for tuning or
            selection.
          </p>
        </header>

        <section className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full min-w-[900px] text-left text-sm">
            <caption className="sr-only">Eight-method model comparison, primary and clause protocols</caption>
            <thead className="bg-secondary/50">
              <tr>
                <th scope="col" className="p-3 font-semibold">Protocol</th>
                <th scope="col" className="p-3 font-semibold">Method</th>
                <th scope="col" className="p-3 font-semibold">Configuration</th>
                <th scope="col" className="p-3 font-semibold">Representation</th>
                <th scope="col" className="p-3 font-semibold">CV macro F1 (±SD)</th>
                <th scope="col" className="p-3 font-semibold">Val macro F1</th>
                <th scope="col" className="p-3 font-semibold">Risky precision / recall</th>
                <th scope="col" className="p-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {COMPARISON_ROWS.map((row, i) => (
                <tr key={`${row.protocol}-${i}`} className={row.status === "Production model" ? "bg-secondary/50" : ""}>
                  <td className="p-3">{row.protocol}</td>
                  <td className="p-3 font-medium">{row.model}</td>
                  <td className="p-3 text-xs text-muted-foreground">{row.config}</td>
                  <td className="p-3 text-xs text-muted-foreground">{row.representation}</td>
                  <td className="p-3 font-mono text-xs">
                    {row.cvMacroF1} (±{row.cvMacroF1Std})
                  </td>
                  <td className="p-3 font-mono text-xs">{row.valMacroF1}</td>
                  <td className="p-3 font-mono text-xs">
                    {row.riskyPrecision} / {row.riskyRecall}
                  </td>
                  <td className="p-3 text-xs font-medium">
                    {row.status === "Production model" ? (
                      <span className="rounded-md bg-secondary px-2 py-0.5 text-secondary-foreground text-[10px]">
                        Production model
                      </span>
                    ) : (
                      row.status
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="space-y-3 text-sm leading-relaxed text-muted-foreground">
          <h2 className="text-xl font-semibold text-foreground">How to read these numbers</h2>
          <p>
            CV macro F1 is computed on the three fixed group-respecting development folds, with
            TF-IDF/SVD refit inside each fold. Validation macro F1 is evaluated on held-out
            validation data after refitting on all training data. These are development results —
            not complete-document performance, probability of correctness, legal safety, or
            expected accuracy on arbitrary uploads.
          </p>
          <p>
            <strong>{PRODUCTION_MODEL.name}</strong> is the strongest method on validation macro F1
            and is the deployed production model at{" "}
            <code>{PRODUCTION_MODEL.path}</code>. Its advantage over the next method is small and
            should not be over-interpreted without significance analysis.
          </p>
          <p>
            <strong>Training time is not dominated by Linear SVM.</strong> Multinomial Naive Bayes
            and KNN have lower classifier fitting times; Linear SVM&apos;s measured total fit time
            includes TF-IDF vectorizer fitting. Training and inference cost figures include
            feature processing and are reported separately in the cost analysis.
          </p>
          <p>
            <strong>Representation:</strong> NB, Logistic Regression, and Linear SVM use sparse
            word unigram/bigram TF-IDF. RBF SVM, Decision Tree, Random Forest, KNN, and Gradient
            Boosting use a training-fold TruncatedSVD-100 dense projection because those
            algorithms require dense input. SVD is a feature transform, not a classifier; differing
            feature pipelines are explicitly labelled and do not isolate algorithm/kernel
            differences.
          </p>
          <p>
            <strong>Gradient Boosting</strong> uses sklearn&apos;s{" "}
            <code>HistGradientBoostingClassifier</code>. No separate boosting library (AdaBoost,
            XGBoost, etc.) is added. Sentence embeddings, voting, stacking, and K-means are not
            part of the final scope.
          </p>
          <p>
            Full per-class metrics, confusion matrices, ROC/PR curve data, and run metadata are in{" "}
            <code>{"results/comparison/{primary,clause}/comparison.csv"}</code> and each model folder
            under <code>{"models/"}</code>. The locked test evaluation is recorded in{" "}
            <code>{"docs/LOCKED_TEST_EVALUATION_v1.md"}</code>.
          </p>
        </section>

        <Link href="/about"><Button variant="outline">Read methodology and limitations</Button></Link>
      </article>
    </div>
  );
}
