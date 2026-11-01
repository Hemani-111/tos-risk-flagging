"""Phase 3 descriptive analysis on included training + validation rows only."""

from __future__ import annotations

import html
import json
import re
import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_split_bundle  # noqa: E402

OUT = ROOT / "results" / "eda" / "v1"
LABEL_ORDER = ["Risky", "Neutral", "Safe"]
COLORS = {"Risky": "#c44e52", "Neutral": "#4c72b0", "Safe": "#55a868"}


def visible_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", str(value)))).strip()


def syllables(word: str) -> int:
    """A small English syllable heuristic used only for descriptive readability."""
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and count > 1 and not word.endswith(("le", "ye")):
        count -= 1
    return max(1, count)


def lexical_features(text: str) -> dict[str, float | int]:
    words = re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)*|\d+", text.lower(), flags=re.UNICODE)
    sentences = [x for x in re.split(r"(?<=[.!?])\s+|[.!?]+", text) if x.strip()]
    sentence_count = max(1, len(sentences))
    word_count = len(words)
    syllable_count = sum(syllables(word) for word in words if word.isalpha())
    ease = (
        206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / max(1, word_count))
        if word_count
        else np.nan
    )
    negated = bool(re.search(
        r"\b(?:not|no|never|without|neither|nor|cannot|can't|cannot|don't|doesn't|didn't|won't|isn't|aren't|wasn't|weren't)\b",
        text.lower(),
    ))
    return {
        "word_count": word_count,
        "sentence_count_proxy": sentence_count,
        "mean_word_length": float(np.mean([len(w) for w in words])) if words else 0.0,
        "syllable_count_heuristic": syllable_count,
        "flesch_reading_ease_heuristic": float(ease),
        "contains_negation": int(negated),
    }


def savefig(path: Path, caption: str) -> None:
    plt.figtext(0.01, 0.005, caption, ha="left", va="bottom", fontsize=8, wrap=True)
    plt.tight_layout(rect=(0, 0.06, 1, 1))
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame, split_metadata = load_split_bundle("primary", ROOT)
    dev = frame.loc[
        frame["primary_include"] & frame["primary_partition"].isin(["train", "validation"])
    ].copy()
    if dev["primary_partition"].eq("test").any():
        raise AssertionError("Locked test rows entered EDA")
    dev["visible_text"] = dev["quote_text"].map(visible_text)
    dev["dev_split"] = dev["primary_partition"]
    dev["lexical"] = dev["visible_text"].map(lexical_features)
    lexical = pd.DataFrame(dev["lexical"].tolist(), index=dev.index)
    for column in lexical:
        dev[column] = lexical[column]

    class_counts = dev["label"].value_counts().reindex(LABEL_ORDER, fill_value=0).rename_axis("label").reset_index(name="rows")
    class_counts["share"] = class_counts["rows"] / len(dev)
    class_counts.to_csv(OUT / "dev_class_counts.csv", index=False)

    topic_counts = pd.crosstab(dev["topic_title"], dev["label"]).reindex(columns=LABEL_ORDER, fill_value=0)
    topic_counts["total"] = topic_counts.sum(axis=1)
    topic_counts.sort_values("total", ascending=False).to_csv(OUT / "topic_label_counts.csv")
    topic_rates = topic_counts[LABEL_ORDER].div(topic_counts["total"].replace(0, np.nan), axis=0)
    topic_rates["total"] = topic_counts["total"]
    topic_rates.sort_values("total", ascending=False).to_csv(OUT / "topic_label_rates.csv")

    services = pd.read_csv(ROOT / "data" / "raw" / "services.csv", usecols=["id", "name"])
    dev["service_key"] = dev["service_id"].astype("Int64").astype(str)
    services["service_key"] = services["id"].astype("Int64").astype(str)
    service_counts = dev.groupby("service_key").size().rename("rows").reset_index()
    service_counts = service_counts.merge(services[["service_key", "name"]], on="service_key", how="left", validate="one_to_one")
    service_label = pd.crosstab(dev["service_key"], dev["label"]).reindex(columns=LABEL_ORDER, fill_value=0)
    service_label["total"] = service_label.sum(axis=1)
    service_counts = service_counts.merge(service_label.reset_index(), on="service_key", validate="one_to_one")
    service_counts.sort_values("rows", ascending=False).to_csv(OUT / "service_label_counts.csv", index=False)

    length_summary = dev.groupby("label").agg(
        rows=("point_id", "size"),
        mean_chars=("visible_text", lambda x: x.str.len().mean()),
        median_chars=("visible_text", lambda x: x.str.len().median()),
        p90_chars=("visible_text", lambda x: x.str.len().quantile(0.90)),
        mean_words=("word_count", "mean"),
        median_words=("word_count", "median"),
        mean_sentences_proxy=("sentence_count_proxy", "mean"),
        mean_word_length=("mean_word_length", "mean"),
        mean_reading_ease_heuristic=("flesch_reading_ease_heuristic", "mean"),
    ).reindex(LABEL_ORDER)
    length_summary.to_csv(OUT / "complexity_by_label.csv")
    negation = dev.groupby("label").agg(rows=("point_id", "size"),
                                        clauses_with_negation=("contains_negation", "sum"))
    negation["share_with_negation"] = negation["clauses_with_negation"] / negation["rows"]
    negation.to_csv(OUT / "negation_by_label.csv")

    clean_quotes = dev["visible_text"].tolist()
    vectorizer = CountVectorizer(ngram_range=(1, 2), min_df=15, max_features=40000,
                                 token_pattern=r"(?u)\b[\w'-]+\b", lowercase=True)
    matrix = vectorizer.fit_transform(clean_quotes)
    terms = np.asarray(vectorizer.get_feature_names_out())
    labels = dev["label"].to_numpy()
    phrase_rows = []
    alpha = 0.5
    vocab_size = max(1, len(terms))
    for label in LABEL_ORDER:
        selected = labels == label
        class_counts_ngram = np.asarray(matrix[selected].sum(axis=0)).ravel()
        other_counts_ngram = np.asarray(matrix[~selected].sum(axis=0)).ravel()
        log_odds = np.log((class_counts_ngram + alpha) / (class_counts_ngram.sum() + alpha * vocab_size)) - np.log(
            (other_counts_ngram + alpha) / (other_counts_ngram.sum() + alpha * vocab_size)
        )
        top = np.argsort(log_odds)[-30:][::-1]
        for rank, idx in enumerate(top, 1):
            phrase_rows.append({
                "label": label, "rank": rank, "ngram": terms[idx],
                "development_document_count_for_ngram": int(class_counts_ngram[idx]),
                "log_odds_vs_other_labels": float(log_odds[idx]),
                "method": "add-0.5 smoothed class-vs-rest term-frequency log odds; min_df=15, word uni/bigrams",
            })
    phrases = pd.DataFrame(phrase_rows)
    phrases.to_csv(OUT / "class_associated_ngrams.csv", index=False)

    # Figure 1: class sample composition.
    plt.figure(figsize=(7, 4.5))
    ordered = class_counts.set_index("label").loc[LABEL_ORDER]
    plt.bar(ordered.index, ordered["rows"], color=[COLORS[x] for x in ordered.index])
    plt.ylabel("Development clauses")
    plt.title("English benchmark labels in development data")
    for i, value in enumerate(ordered["rows"]):
        plt.text(i, value, f"{value:,}\n{value / len(dev):.1%}", ha="center", va="bottom", fontsize=9)
    savefig(OUT / "class_balance.png", f"N={len(dev):,} included train+validation clauses; locked test rows excluded. Counts describe this curated sample.")

    # Figure 2: label composition for the 15 most frequent topics.
    top_topics = topic_counts.sort_values("total", ascending=False).head(15)
    topic_share = top_topics[LABEL_ORDER].div(top_topics["total"], axis=0).sort_index()
    plt.figure(figsize=(9, 7))
    left = np.zeros(len(topic_share))
    for label in LABEL_ORDER:
        values = topic_share[label].to_numpy()
        plt.barh(topic_share.index, values, left=left, color=COLORS[label], label=label)
        left += values
    plt.xlabel("Share of annotated clauses within topic")
    plt.title("Label composition in the 15 largest development topics")
    plt.legend(title="Dataset label", bbox_to_anchor=(1.02, 1), loc="upper left")
    savefig(OUT / "topic_label_composition.png", f"N={len(dev):,}; topic and label fields are retrospective annotations, not inference-time features.")

    # Figure 3: word-count distribution, with a log axis for long-tailed legal excerpts.
    plt.figure(figsize=(8, 5))
    groups = [dev.loc[dev["label"].eq(label), "word_count"].clip(lower=1).to_numpy() for label in LABEL_ORDER]
    plt.boxplot(groups, tick_labels=LABEL_ORDER, showfliers=False, whis=(5, 95))
    plt.yscale("log")
    plt.ylabel("Words per clause (log scale; whiskers 5th–95th percentile)")
    plt.title("Excerpt length by dataset label")
    savefig(OUT / "word_count_by_label.png", f"N={len(dev):,}; descriptive association only, not evidence that length causes risk labels.")

    # Figure 4: sampled-service concentration.
    ranked = service_counts.sort_values("rows", ascending=False).reset_index(drop=True)
    cumulative = ranked["rows"].cumsum() / ranked["rows"].sum()
    plt.figure(figsize=(7, 5))
    plt.plot(np.arange(1, len(ranked) + 1) / len(ranked), cumulative, color="#4c72b0", lw=2)
    plt.plot([0, 1], [0, 1], color="#888888", linestyle="--", lw=1)
    plt.xlabel("Cumulative share of represented services")
    plt.ylabel("Cumulative share of development clauses")
    plt.title("Clause concentration across represented services")
    savefig(OUT / "service_concentration.png", f"N={len(dev):,}; {len(ranked):,} represented services. Sampling concentration is not a real-world service risk ranking.")

    # Figure 5: strongest positive class-associated phrases.
    fig, axes = plt.subplots(1, 3, figsize=(15, 7))
    for ax, label in zip(axes, LABEL_ORDER):
        subset = phrases.loc[phrases["label"].eq(label)].head(12).sort_values("log_odds_vs_other_labels")
        ax.barh(subset["ngram"], subset["log_odds_vs_other_labels"], color=COLORS[label])
        ax.set_title(label)
        ax.set_xlabel("Smoothed log-odds vs other labels")
    fig.suptitle("Phrases associated with dataset labels")
    savefig(OUT / "class_associated_phrases.png", f"N={len(dev):,}; unigram/bigram counts from development text. Associations are affected by case-derived labels and context.")

    sizes = service_counts["rows"].sort_values(ascending=False).to_numpy()
    top_shares = {
        "top_1_service_clause_share": float(sizes[:1].sum() / sizes.sum()),
        "top_10_services_clause_share": float(sizes[:10].sum() / sizes.sum()),
        "top_50_services_clause_share": float(sizes[:50].sum() / sizes.sum()),
        "service_hhi": float(np.square(sizes / sizes.sum()).sum()),
        "top_services": service_counts.sort_values("rows", ascending=False).head(20).to_dict("records"),
    }
    summary = {
        "analysis_date": date.today().isoformat(),
        "split_id": split_metadata["split_id"],
        "source_dataset": split_metadata["dataset"],
        "source_dataset_sha256": split_metadata["dataset_sha256"],
        "protocol": "primary development only: included train + validation; locked test excluded",
        "development_rows": int(len(dev)),
        "training_rows": int(dev["dev_split"].eq("train").sum()),
        "validation_rows": int(dev["dev_split"].eq("validation").sum()),
        "labels": {str(k): int(v) for k, v in dev["label"].value_counts().sort_index().items()},
        "topics": int(dev["topic_title"].nunique()),
        "services": int(dev["service_id"].nunique()),
        "documents": int(dev["document_id"].nunique()),
        "service_concentration": top_shares,
        "ngram_method": "CountVectorizer word unigrams/bigrams; min document frequency 15, max vocabulary 40,000; add-0.5 smoothed class-vs-rest term-frequency log odds. Negation terms retained.",
        "readability_method": "Flesch Reading Ease form with a simple English syllable-group heuristic; report as rough proxy only.",
        "limitations": [
            "Topic, service, and dataset label fields are available only retrospectively; they are not model input features.",
            "Labels are case-derived annotations, so phrase/length/topic associations do not establish causal or legal risk.",
            "The readability value is a heuristic and short excerpt sentence counts are imperfect.",
            "No model has been trained yet; error-rate analysis is deferred until Phase 4/5 development predictions exist.",
            "These plots describe curated development excerpts, not all clauses in policies or all services.",
        ],
        "figures": {
            "class_balance.png": f"English development label counts (N={len(dev):,}); locked test excluded.",
            "topic_label_composition.png": "Within-topic class shares for the 15 most represented topics; retrospective labels only.",
            "word_count_by_label.png": "Word-count distribution by dataset label; log scale and 5th–95th percentile whiskers.",
            "service_concentration.png": "Cumulative clause share across services represented in development; not a service safety rank.",
            "class_associated_phrases.png": "Top smoothed log-odds unigrams/bigrams by label; negation retained; associative only.",
        },
    }
    (OUT / "eda_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report_lines = [
        "# Phase 3 EDA v1", "",
        f"**Scope:** included primary-protocol training and validation rows only (N={len(dev):,}); locked test rows were excluded.", "",
        "## Questions and observations", "",
        f"- **Is the sample balanced?** {', '.join(f'{r.label}: {int(r.rows):,} ({r.share:.1%})' for r in class_counts.itertuples())}. This is the curated English excerpt sample, not population prevalence.",
        f"- **Which topics carry which annotations?** `topic_label_counts.csv` and `topic_label_composition.png` report counts and within-topic shares. Topic labels are attached retrospectively and cannot be used for arbitrary uploads.",
        f"- **Does excerpt complexity vary by label?** `complexity_by_label.csv` reports length, word/sentence proxies, and a rough readability score. These are descriptive associations, not causal effects; the syllable estimate is heuristic.",
        f"- **Which phrases are associated with labels?** `class_associated_ngrams.csv` and `class_associated_phrases.png` rank development-only word unigrams/bigrams by smoothed log odds. Negation was retained. Association reflects case-derived annotation and context.",
        f"- **Are some services overrepresented?** {len(service_counts):,} services appear in development. Top 1/10/50 services contribute {top_shares['top_1_service_clause_share']:.1%}/{top_shares['top_10_services_clause_share']:.1%}/{top_shares['top_50_services_clause_share']:.1%} of rows. The concentration curve describes sample collection, not real-world service risk.",
        "- **What is hard to classify?** No model is trained, so error analysis is deferred; do not infer error rates from descriptive counts.",
        "- **Do semantic groups emerge?** No clustering was run: it is optional and not needed to answer the current research questions.", "",
        "## Outputs", "",
        "CSV tables: `dev_class_counts.csv`, `topic_label_counts.csv`, `topic_label_rates.csv`, `service_label_counts.csv`, `complexity_by_label.csv`, `negation_by_label.csv`, `class_associated_ngrams.csv`.",
        "Figures: class balance, topic composition, word-count distribution, service concentration, and associated phrases. Figure captions state sample sizes and interpretation limits.", "",
        "## Feature and leakage decisions", "",
        "Only quote text is available for prediction. Dataset topic titles, services, case IDs, and labels are retrospective audit fields and must not be predictive features. Preserve negation and legal wording; remove markup only in the descriptive phrase-count representation, not by altering the source quote. Fit future vectorizers and feature transforms inside each training fold.", "",
        "## Limitations", "",
        "The label target is case-derived rather than an independently adjudicated excerpt judgment. The English screen and readability score are approximate. There are no model errors yet, and no locked-test text was included in these analyses. Results describe only the included development subset.", "",
    ]
    (OUT / "EDA_REPORT.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(json.dumps({"output": str(OUT), "development_rows": len(dev), "labels": summary["labels"], "topics": summary["topics"], "services": summary["services"], "top_10_service_share": top_shares["top_10_services_clause_share"]}, indent=2))


if __name__ == "__main__":
    main()
