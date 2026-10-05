import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Upload, ShieldCheck, FileText, Search, ChevronRight } from "lucide-react";

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="py-20 sm:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
              Read the fine print.
              <br />
              Know the risk.
            </h1>
            <p className="mt-6 text-lg text-muted-foreground">
              Upload a Terms of Service or Privacy Policy and instantly identify
              clauses that deserve a closer look.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/analyze">
                <Button size="lg" className="w-full sm:w-auto">
                  <Upload className="mr-2 h-4 w-4" />
                  Analyze a document
                </Button>
              </Link>
              <Link href="#how-it-works">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  See how it works
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
      
      {/* How it works */}
      <section id="how-it-works" className="border-t border-border bg-secondary/30 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-2xl font-semibold">How it works</h2>
            <p className="mt-2 text-muted-foreground">
              Three simple steps to understand what you&apos;re agreeing to.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground mb-4">
                <span className="text-lg font-semibold">01</span>
              </div>
              <h3 className="text-base font-medium mb-2">Upload</h3>
              <p className="text-sm text-muted-foreground">
                Drop your Terms of Service or Privacy Policy document.
              </p>
            </div>
            
            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground mb-4">
                <span className="text-lg font-semibold">02</span>
              </div>
              <h3 className="text-base font-medium mb-2">Analyze</h3>
              <p className="text-sm text-muted-foreground">
                We analyze each clause and classify it as Safe, Neutral, or Risky.
              </p>
            </div>
            
            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground mb-4">
                <span className="text-lg font-semibold">03</span>
              </div>
              <h3 className="text-base font-medium mb-2">Review</h3>
              <p className="text-sm text-muted-foreground">
                Review what deserves attention and make informed decisions.
              </p>
            </div>
          </div>
        </div>
      </section>
      
      {/* Features */}
      <section className="py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-2xl font-semibold">Built for clarity, not legal jargon</h2>
            <p className="mt-2 text-muted-foreground">
              project name makes complex legal documents understandable.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-5xl mx-auto">
            <div className="text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-muted mb-4">
                <FileText className="h-5 w-5 text-muted-foreground" />
              </div>
              <h3 className="text-sm font-medium mb-1">Clause-level analysis</h3>
              <p className="text-xs text-muted-foreground">
                Every clause is analyzed individually for precise risk assessment.
              </p>
            </div>
            
            <div className="text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-muted mb-4">
                <Search className="h-5 w-5 text-muted-foreground" />
              </div>
              <h3 className="text-sm font-medium mb-1">Topic identification</h3>
              <p className="text-xs text-muted-foreground">
                Automatically identifies what each clause is about.
              </p>
            </div>
            
            <div className="text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-muted mb-4">
                <ShieldCheck className="h-5 w-5 text-muted-foreground" />
              </div>
              <h3 className="text-sm font-medium mb-1">Document summary</h3>
              <p className="text-xs text-muted-foreground">
                Get an overall assessment of the document&apos;s risk profile.
              </p>
            </div>
            
            <div className="text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-muted mb-4">
                <FileText className="h-5 w-5 text-muted-foreground" />
              </div>
              <h3 className="text-sm font-medium mb-1">Full document view</h3>
              <p className="text-xs text-muted-foreground">
                Read the complete document with clause-level detail.
              </p>
            </div>
          </div>
        </div>
      </section>
      
      {/* CTA */}
      <section className="border-t border-border bg-secondary/30 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-2xl font-semibold">Ready to understand your terms?</h2>
            <p className="mt-4 text-muted-foreground">
              Upload a document and see what project name finds in seconds.
            </p>
            <div className="mt-8">
              <Link href="/analyze">
                <Button size="lg">
                  <Upload className="mr-2 h-4 w-4" />
                  Analyze a document
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
      
      {/* Disclaimer */}
      <section className="border-t border-border py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs text-muted-foreground">
            project name is an educational screening tool and does not provide legal advice.
            Always consult a qualified legal professional for legal matters.
          </p>
        </div>
      </section>
    </div>
  );
}
