import Link from "next/link";
import { Button } from "@/components/ui/Button";

const rows = [
  {
    protocol: "Primary unseen-service",
    model: "Linear SVM",
    config: "word unigram/bigram TF-IDF, C=1, class_weight=balanced",
    representation: "Sparse TF-IDF",
    cvMacroF1: "0.8206",
    valMacroF1: "0.8206",
    risky: "0.7886 / 0.8461",
    status: "Production model",
  },
  {
    protocol: "Primary unseen-service",
    model: "Logistic Regression",
    config: "word unigram/bigram TF-IDF, C=1, class_weight=None",
    representation: "Sparse TF-IDF",
    cvMacroF1: "0.8185",
    valMacroF1: "0.8185",
    risky: "0.7941 / 0.8345",
    status: "Baseline",
  },
  {
    protocol: "Primary unseen-service",
    model: "SVM — RBF",
    config: "SVD-100 dense, C=1, gamma=scale",
    representation: "Dense (SVD-100)",
    cvMacroF1: "0.8064",
    valMacroF1: "0.8064",
    risky: "0.7936 / 0.8056",
    status: "Baseline",
  },
  {
    protocol: "Primary unseen-service",
    model: "Multinomial Naive Bayes",
    config: "word unigram/bigram TF-IDF, alpha=0.1",
    representation: "Sparse TF-IDF",
    cvMacroF1: "0.7980",
    valMacroF1: "0.7980",
    risky: "0.7370 / 0.8368",
    status: "Baseline",
  },
  {
    protocol: "Primary unseen-service",
    model: "Gradient Boosting",
    config: "SVD-100 dense, HistGradientBoosting, lr=0.1, iter=200",
    representation: "Dense (SVD-100)",
    cvMacroF1: "0.7867",
    valMacroF1: "0.7867",
    risky: "0.7719 / 0.7870",
    status: "End-semester addition",
  },
  {
    protocol: "Primary unseen-service",
    model: "K-Nearest Neighbours",
    config: "SVD-100 dense, k=15, distance weighting",
    representation: "Dense (SVD-100)",
    cvMacroF1: "0.7837",
    valMacroF1: "0.7837",
    risky: "0.7843 / 0.7743",
    status: "End-semester addition",
  },
  {
    protocol: "Primary unseen-service",
    model: "Random Forest",
    config: "SVD-100 dense, 200 trees, max_depth=None",
    representation: "Dense (SVD-100)",
    cvMacroF1: "0.7828",
    valMacroF1: "0.7828",
    risky: "0.7632 / 0.7836",
    status: "End-semester addition",
  },
  {
    protocol: "Primary unseen-service",
    model: "Decision Tree",
    config: "SVD-100 dense, max_depth=30, min_samples_leaf=10",
    representation: "Dense (SVD-100)",
    cvMacroF1: "0.6366",
    valMacroF1: "0.6366",
    risky: "0.6075 / 0.6412",
    status: "End-semester addition",
  },
];

export default function ResearchPage() {
  return (
    <div className="py-12 sm:py-16">
      <article className="mx-auto max-w-6xl space-y-8 px-4 sm:px-6">
        <header>
          <p className="text-sm font-medium text-muted-foreground">Model comparison</p>
          <h1 className="mt-2 text-3xl font-semibold">Standard classifier comparison</h1>
          <p className="mt-4 max-w-3xl leading-relaxed text-muted-foreground">
            All eight methods were trained and tuned on the same prepared development data with
            fixed group-respecting splits. Macro F1 is the selection metric; Risky precision and
            recall are reported alongside. The locked test partition was not used for tuning or
            selection.
          </p>
        </header>

        <section className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full min-w-[700px] text-left text-sm">
            <caption className="sr-only">Eight-method model comparison, primary protocol</caption>
            <thead className="bg-secondary/50">
              <tr>
                <th scope="col" className="p-3 font-semibold">Protocol</th>
                <th scope="col" className="p-3 font-semibold">Method</th>
                <th scope="col" className="p-3 font-semibold">Configuration</th>
                <th scope="col" className="p-3 font-semibold">Representation</th>
                <th scope="col" className="p-3 font-semibold">Validation macro F1</th>
                <th scope="col" className="p-3 font-semibold">Risky precision / recall</th>
                <th scope="col" className="p-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {rows.map((row, i) => (
                <tr key={i} className={row.status === "Production model" ? "bg-secondary/50" : ""}>
                  <td className="p-3">{row.protocol}</td>
                  <td className="p-3 font-medium">{row.model}</td>
                  <td className="p-3 text-xs text-muted-foreground">{row.config}</td>
                  <td className="p-3 text-xs text-muted-foreground">{row.representation}</td>
                  <td className="p-3 font-mono text-xs">{row.valMacroF1}</td>
                  <td className="p-3 font-mono text-xs">{row.risky}</td>
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
            These are <strong>validation</strong> results on fixed group-respecting splits of the
            prepared English development data (13,439 train / 2,658 validation rows for the primary
            protocol). They are not complete-document performance, probability of correctness, legal
            safety, or expected accuracy on arbitrary uploads.
          </p>
          <p>
            <strong>Linear SVM</strong> is the strongest method on macro F1 (0.8206) and is the
            deployed production model at <code>models/releases/linear-svc-primary-v2/</code>. It is
            also the fastest to train (~0.2 s) and keeps the TF-IDF matrix sparse.
          </p>
          <p>
            <strong>Representation:</strong> NB, Logistic Regression, and Linear SVM use sparse word
            unigram/bigram TF-IDF. RBF SVM, Decision Tree, Random Forest, KNN, and Gradient Boosting
            use a training-fold TruncatedSVD (100 components) dense projection because those
            algorithms require dense input. SVD is a feature transform, not a classifier; differing
            feature pipelines are explicitly labelled.
          </p>
          <p>
            <strong>Gradient Boosting</strong> uses sklearn&apos;s
            <code>HistGradientBoostingClassifier</code>. No separate boosting library (AdaBoost,
            XGBoost, etc.) is added. Sentence embeddings, voting, stacking, and K-means are not part
            of the final scope.
          </p>
          <p>
            Full per-class metrics, confusion matrices, and run metadata are in{" "}
            <code>results/comparison/primary/comparison.csv</code> and each model folder under{" "}
            <code>models/</code>. The locked test evaluation is recorded in{" "}
            <code>docs/LOCKED_TEST_EVALUATION_v1.md</code>.
          </p>
        </section>

        <Link href="/about"><Button variant="outline">Read methodology and limitations</Button></Link>
      </article>
    </div>
  );
}
