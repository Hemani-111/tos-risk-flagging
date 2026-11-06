import { useMemo, useRef, useState } from "react";
import {
  FiAlertTriangle,
  FiAlignLeft,
  FiArrowUpRight,
  FiCheckCircle,
  FiChevronDown,
  FiChevronUp,
  FiDownload,
  FiEdit3,
  FiFileText,
  FiInfo,
  FiLayers,
  FiMaximize2,
  FiMinusCircle,
  FiSearch,
  FiType,
  FiTrash2,
  FiX,
} from "react-icons/fi";
import "./ReviewPage.css";

// Replace this illustrative sample with the analysis response from your API.
const SAMPLE_DOCUMENT = {
  filename: "example-policy.txt",
  title: "Privacy policy",
  sections: [
    {
      heading: "1. About this policy",
      clauses: [
        {
          id: "c1",
          label: "Neutral",
          text: "This policy describes how Example Service handles information when you use our website.",
        },
      ],
    },
    {
      heading: "2. Information we collect",
      clauses: [
        {
          id: "c2",
          label: "Neutral",
          text: "We collect the account details you provide, including your name and email address.",
        },
        {
          id: "c3",
          label: "Neutral",
          text: "We collect device and usage information to operate the service and understand how it is used.",
        },
      ],
    },
    {
      heading: "3. Sharing information",
      clauses: [
        {
          id: "c4",
          label: "Risky",
          text: "We may share your information with advertising partners.",
        },
        {
          id: "c5",
          label: "Neutral",
          text: "We also use service providers to support hosting, analytics, and customer support.",
        },
      ],
    },
    {
      heading: "4. Your choices",
      clauses: [
        {
          id: "c6",
          label: "Safe",
          text: "You can request deletion of your account and associated personal information.",
        },
        {
          id: "c8",
          label: "Safe",
          text: "You may opt out of marketing emails through the unsubscribe link in each message.",
        },
      ],
    },
    {
      heading: "5. Changes to this policy",
      clauses: [
        {
          id: "c7",
          label: "Risky",
          text: "We may change these terms at any time without notifying you individually.",
        },
      ],
    },
    {
      heading: "6. Dispute resolution",
      clauses: [
        {
          id: "c9",
          label: "Risky",
          text: "Disputes must be resolved through binding arbitration rather than a court trial.",
        },
      ],
    },
    {
      heading: "7. Contact us",
      clauses: [
        {
          id: "c10",
          label: "Neutral",
          text: "Contact our support team if you have questions about this policy.",
        },
      ],
    },
  ],
};

const LABELS = ["All", "Risky", "Neutral", "Safe"];

function flattenClauses(sections) {
  return sections.flatMap((section) =>
    section.clauses.map((clause) => ({
      ...clause,
      section: section.heading,
    })),
  );
}

function segmentSource(text, clauses) {
  if (!text) return [];
  const ordered = [...clauses]
    .filter((clause) => Number.isInteger(clause.startOffset) && Number.isInteger(clause.endOffset) &&
      clause.startOffset >= 0 && clause.endOffset > clause.startOffset && clause.endOffset <= text.length)
    .sort((left, right) => left.startOffset - right.startOffset || left.endOffset - right.endOffset);
  const segments = [];
  let cursor = 0;
  for (const clause of ordered) {
    if (clause.startOffset < cursor) continue;
    if (clause.startOffset > cursor) segments.push({ start: cursor, end: clause.startOffset, clause: null });
    segments.push({ start: clause.startOffset, end: clause.endOffset, clause });
    cursor = clause.endOffset;
  }
  if (cursor < text.length) segments.push({ start: cursor, end: text.length, clause: null });
  return segments;
}

function downloadFile(filename, contents, type) {
  const blob = new Blob([contents], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function ReviewPage({
  documentData = SAMPLE_DOCUMENT,
  illustrative = documentData === SAMPLE_DOCUMENT,
  onNewAnalysis,
  onClear,
}) {
  const clauses = useMemo(
    () => documentData.clauses?.length ? documentData.clauses : flattenClauses(documentData.sections ?? []),
    [documentData.clauses, documentData.sections],
  );
  const sourceSegments = useMemo(
    () => !illustrative && documentData.extractedText ? segmentSource(documentData.extractedText, clauses) : [],
    [clauses, documentData.extractedText, illustrative],
  );
  const [selectedId, setSelectedId] = useState(clauses[0]?.id ?? null);
  const [filter, setFilter] = useState("All");
  const [query, setQuery] = useState("");
  const [showHighlights, setShowHighlights] = useState(true);
  const [fontSize, setFontSize] = useState(16);
  const [focusedReader, setFocusedReader] = useState(false);
  const [mobilePane, setMobilePane] = useState("document");
  const [exportOpen, setExportOpen] = useState(false);
  const documentRef = useRef(null);
  const clauseRefs = useRef({});

  const counts = useMemo(
    () =>
      clauses.reduce(
        (result, clause) => {
          result[clause.label] = (result[clause.label] ?? 0) + 1;
          return result;
        },
        { Risky: 0, Neutral: 0, Safe: 0 },
      ),
    [clauses],
  );

  const visibleClauses = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return clauses.filter((clause) => {
      const matchesLabel = filter === "All" || clause.label === filter;
      const matchesText =
        !normalizedQuery ||
        `${clause.text} ${clause.section}`.toLowerCase().includes(normalizedQuery);
      return matchesLabel && matchesText;
    });
  }, [clauses, filter, query]);

  function selectClause(id, source = "list") {
    setSelectedId(id);
    if (source === "list") {
      setMobilePane("document");
      requestAnimationFrame(() => {
        document.getElementById(`source-${id}`)?.scrollIntoView({
          behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
            ? "auto"
            : "smooth",
          block: "center",
        });
      });
    } else {
      setFilter("All");
      setQuery("");
      setMobilePane("clauses");
      requestAnimationFrame(() =>
        clauseRefs.current[id]?.scrollIntoView({ block: "nearest" }),
      );
    }
  }

  function moveSelection(direction) {
    if (!visibleClauses.length) return;
    const currentIndex = visibleClauses.findIndex((item) => item.id === selectedId);
    const nextIndex =
      currentIndex < 0
        ? 0
        : (currentIndex + direction + visibleClauses.length) % visibleClauses.length;
    selectClause(visibleClauses[nextIndex].id, "list");
  }

  function exportJSON() {
    downloadFile(
      "termsguard-clauses.json",
      JSON.stringify(
        {
          filename: documentData.filename,
          illustrative,
          notice: illustrative ? "Illustrative sample data; not model predictions." : undefined,
          clauses,
        },
        null,
        2,
      ),
      "application/json",
    );
    setExportOpen(false);
  }

  function exportCSV() {
    const quote = (value) => `"${String(value).replaceAll('"', '""')}"`;
    const rows = [
      ["id", "label", "section", "text"],
      ...clauses.map(({ id, label, section, text }) => [id, label, section, text]),
    ];
    const csv = [
      illustrative ? '"Illustrative sample data; not model predictions."' : "",
      ...rows.map((row) => row.map(quote).join(",")),
    ]
      .filter(Boolean)
      .join("\n");
    downloadFile("termsguard-clauses.csv", csv, "text/csv;charset=utf-8");
    setExportOpen(false);
  }

  function cycleTextSize() {
    setFontSize((current) => (current >= 20 ? 16 : current + 2));
  }

  return (
    <main className="tg-review-page">
      <header className="tg-review-header">
        <a className="tg-brand" href="/" aria-label="TermsGuard home">
          <span className="tg-brand-icon"><FiFileText aria-hidden="true" /></span>
          <span>TermsGuard</span>
        </a>
        <div className="tg-header-tag"><span />{illustrative ? "Sample workspace" : "Document review"}</div>
      </header>

      <div className="tg-page-shell">
        <div className="tg-page-heading">
          <div>
            <div className="tg-eyebrow">Workspace <span>/</span> Document review</div>
            <h1>{documentData.title ?? "Document review"}</h1>
            <div className="tg-file-meta">
              <FiFileText aria-hidden="true" />
              <span>{documentData.filename ?? "Untitled document"}</span>
              {illustrative && <span className="tg-sample-tag">Illustrative sample</span>}
            </div>
          </div>
          <div className="tg-heading-actions">
            <div className="tg-export-wrap">
              <button
                className="tg-button tg-button-secondary"
                type="button"
                onClick={() => setExportOpen((value) => !value)}
                aria-expanded={exportOpen}
              >
                <FiDownload aria-hidden="true" /> Export
              </button>
              {exportOpen && (
                <div className="tg-export-menu" role="menu">
                  <button role="menuitem" onClick={exportCSV}>Download CSV</button>
                  <button role="menuitem" onClick={exportJSON}>Download JSON</button>
                  <button role="menuitem" onClick={() => { window.print(); setExportOpen(false); }}>Print / Save PDF</button>
                </div>
              )}
            </div>
            <button className="tg-button tg-button-primary" type="button" onClick={onNewAnalysis}>
              <span aria-hidden="true">＋</span> New analysis
            </button>
            {onClear && <button className="tg-button tg-button-secondary" type="button" onClick={onClear}><FiTrash2 aria-hidden="true"/> Clear results</button>}
          </div>
        </div>

        <section className="tg-summary" aria-label="Clause label counts">
          <SummaryItem icon={<FiLayers />} value={clauses.length} label="Clauses" detail="In this document" tone="total" />
          <SummaryItem icon={<FiAlertTriangle />} value={counts.Risky} label="Risky" detail="Predicted label" tone="risky" />
          <SummaryItem icon={<FiMinusCircle />} value={counts.Neutral} label="Neutral" detail="Predicted label" tone="neutral" />
          <SummaryItem icon={<FiCheckCircle />} value={counts.Safe} label="Safe" detail="Predicted label" tone="safe" />
        </section>

        <div className="tg-mobile-tabs" role="tablist" aria-label="Review panels">
          <button className={mobilePane === "document" ? "active" : ""} onClick={() => setMobilePane("document")} role="tab" aria-selected={mobilePane === "document"}>Document</button>
          <button className={mobilePane === "clauses" ? "active" : ""} onClick={() => setMobilePane("clauses")} role="tab" aria-selected={mobilePane === "clauses"}>Clauses</button>
        </div>

        <section className={`tg-workspace ${focusedReader ? "tg-reader-focused" : ""} ${mobilePane === "clauses" ? "tg-show-clauses" : ""}`}>
          <section className="tg-reader" aria-label="Extracted document">
            <div className="tg-toolbar">
              <strong><FiAlignLeft aria-hidden="true" /> Extracted document</strong>
              <div className="tg-toolbar-actions">
                <button className="tg-toolbar-button" type="button" aria-pressed={showHighlights} onClick={() => setShowHighlights((value) => !value)}>
                  <FiEdit3 aria-hidden="true" /> {showHighlights ? "Highlights on" : "Highlights off"}
                </button>
                <button className="tg-toolbar-button" type="button" onClick={cycleTextSize} aria-label={`Change document text size; currently ${fontSize} pixels`}>
                  <FiType aria-hidden="true" /> {fontSize} px
                </button>
                <button className="tg-icon-button tg-focus-button" type="button" onClick={() => setFocusedReader((value) => !value)} aria-pressed={focusedReader} aria-label={focusedReader ? "Show clause list" : "Expand document reading area"}>
                  <FiMaximize2 aria-hidden="true" />
                </button>
              </div>
            </div>
            <article className={`tg-document ${showHighlights ? "" : "tg-highlights-hidden"}`} ref={documentRef}>
              <div className="tg-document-title">
                <div className="tg-document-kicker"><span>{illustrative ? "EXAMPLE SERVICE" : "EXTRACTED DOCUMENT"}</span><span>{illustrative ? "POLICY / 01" : (documentData.filename ?? "SOURCE TEXT")}</span></div>
                <h2>{documentData.title ?? "Document"}</h2>
                <p>{illustrative ? "Read each highlighted passage in its full context." : "Extracted text. Original wording is preserved."}</p>
              </div>
              {!illustrative && documentData.extractedText ? (
                <div className="tg-original-text" style={{ fontSize: `${fontSize}px` }} aria-label={`Extracted text from ${documentData.filename ?? "document"}`}>
                  {sourceSegments.map((segment, index) => segment.clause ? (
                    <mark
                      className={`tg-passage tg-label-${segment.clause.label.toLowerCase()} ${selectedId === segment.clause.id ? "selected" : ""}`}
                      key={`${segment.start}-${segment.clause.id}`}
                      id={`source-${segment.clause.id}`}
                      role="button"
                      tabIndex={0}
                      aria-pressed={selectedId === segment.clause.id}
                      aria-label={`Clause ${segment.clause.id}, predicted ${segment.clause.label}: ${segment.clause.text}`}
                      onClick={() => selectClause(segment.clause.id, "document")}
                      onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectClause(segment.clause.id, "document"); } }}
                    >{documentData.extractedText.slice(segment.start, segment.end)}</mark>
                  ) : <span key={`plain-${segment.start}-${index}`}>{documentData.extractedText.slice(segment.start, segment.end)}</span>)}
                </div>
              ) : (documentData.sections ?? []).map((section) => (
                <section className="tg-document-section" key={section.heading}>
                  <h3>{section.heading}</h3>
                  {section.clauses.map((clause) => (
                    <p className="tg-source-paragraph" key={clause.id}>
                      <span className="tg-margin-number" aria-hidden="true">{String(clauses.findIndex((item) => item.id === clause.id) + 1).padStart(2, "0")}</span>
                      <button
                        id={`source-${clause.id}`}
                        className={`tg-passage tg-label-${clause.label.toLowerCase()} ${selectedId === clause.id ? "selected" : ""}`}
                        type="button"
                        onClick={() => selectClause(clause.id, "document")}
                        aria-pressed={selectedId === clause.id}
                        aria-label={`Clause ${clause.id}, predicted ${clause.label}: ${clause.text}`}
                        style={{ fontSize: `${fontSize}px` }}
                      >
                        {clause.text}
                      </button>
                    </p>
                  ))}
                </section>
              ))}
            </article>
          </section>

          <aside className="tg-inspector" aria-label="Clause list">
            <div className="tg-inspector-top">
              <h2>Review clauses <span>/ {clauses.length}</span></h2>
              <label className="tg-search-wrap">
                <FiSearch aria-hidden="true" />
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search clauses…" aria-label="Search clause text or section" />
                {query && <button type="button" aria-label="Clear search" onClick={() => setQuery("")}><FiX /></button>}
              </label>
              <div className="tg-filters" aria-label="Filter clauses by prediction">
                {LABELS.map((label) => {
                  const count = label === "All" ? clauses.length : counts[label];
                  return (
                    <button key={label} type="button" className={filter === label ? "active" : ""} onClick={() => setFilter(label)} aria-pressed={filter === label}>
                      {label}<span>{count}</span>
                    </button>
                  );
                })}
              </div>
              <div className="tg-match-row">
                <span aria-live="polite">Showing {visibleClauses.length} of {clauses.length} clauses</span>
                <div>
                  <button type="button" aria-label="Previous matching clause" disabled={!visibleClauses.length} onClick={() => moveSelection(-1)}><FiChevronUp /></button>
                  <button type="button" aria-label="Next matching clause" disabled={!visibleClauses.length} onClick={() => moveSelection(1)}><FiChevronDown /></button>
                </div>
              </div>
            </div>
            <div className="tg-clause-list">
              {visibleClauses.length ? visibleClauses.map((clause) => (
                <button
                  className={`tg-clause ${selectedId === clause.id ? "selected" : ""}`}
                  type="button"
                  key={clause.id}
                  ref={(node) => { clauseRefs.current[clause.id] = node; }}
                  onClick={() => selectClause(clause.id, "list")}
                  aria-pressed={selectedId === clause.id}
                >
                  <span className="tg-clause-head"><span>Clause {String(clauses.findIndex((item) => item.id === clause.id) + 1).padStart(2, "0")}</span><span className={`tg-badge tg-badge-${clause.label.toLowerCase()}`}>{clause.label}</span></span>
                  <span className="tg-clause-text">{clause.text}</span>
                  <span className="tg-clause-location">{clause.section}<FiArrowUpRight aria-hidden="true" /></span>
                </button>
              )) : (
                <div className="tg-empty">
                  <FiSearch aria-hidden="true" />
                  <strong>No matching clauses</strong>
                  <span>Try another phrase or clear the filters.</span>
                  <button type="button" onClick={() => { setQuery(""); setFilter("All"); }}>Reset search and filters</button>
                </div>
              )}
            </div>
          </aside>
        </section>

        <footer className="tg-review-footer">
          <span><FiInfo aria-hidden="true" /> Educational screening, not legal advice. Labels may be incorrect.</span>
          {illustrative && <span className="tg-preview-note">Sample labels are illustrative.</span>}
          {!illustrative && <details className="tg-analysis-details"><summary>Analysis details</summary><div><span>Model: {documentData.modelVersion ?? "Unknown"}</span><span>Schema: {documentData.schemaVersion ?? "Unknown"}</span>{documentData.warnings?.map((warning,index)=><span key={index}>{warning}</span>)}</div></details>}
        </footer>
      </div>
    </main>
  );
}

function SummaryItem({ icon, value, label, detail, tone }) {
  return (
    <div className="tg-summary-item">
      <span className={`tg-summary-icon tg-tone-${tone}`} aria-hidden="true">{icon}</span>
      <strong>{value}</strong>
      <span className="tg-summary-label">{label}<small>{detail}</small></span>
    </div>
  );
}
