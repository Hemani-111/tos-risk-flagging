export default function AboutPage() {
  return (
    <div className="py-16 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl">
          <h1 className="text-3xl font-semibold mb-6">How it works</h1>
          
          <div className="prose prose-slate max-w-none space-y-8">
            <section>
              <h2 className="text-xl font-semibold mb-4">Methodology</h2>
              <p className="text-muted-foreground">
                project name will use machine learning to analyze Terms of Service and Privacy Policy documents.
                The system will break documents into individual clauses and classify each one.
              </p>
            </section>
            
            <section>
              <h2 className="text-xl font-semibold mb-4">Current status</h2>
              <p className="text-muted-foreground">
                The ML model is not yet connected. Document upload and text input work,
                but clause-level risk analysis is not available until the model is trained and connected.
              </p>
            </section>
            
            <section>
              <h2 className="text-xl font-semibold mb-4">Planned features</h2>
              <p className="text-muted-foreground">
                Once the model is connected, project name will provide clause-level analysis,
                topic identification, risk highlighting, and document-level summaries.
              </p>
            </section>
            
            <section className="rounded-lg border border-border bg-secondary/30 p-6">
              <h2 className="text-xl font-semibold mb-4">Important disclaimer</h2>
              <p className="text-muted-foreground">
                project name is an educational screening tool and does not provide legal advice.
                The analysis is automated and may not capture all nuances of legal documents.
                Always consult a qualified legal professional for legal matters.
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
