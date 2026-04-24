import Link from "next/link";

const features = [
  {
    icon: "🔍",
    title: "Policy X-Ray",
    description: "Turn dense policy language into a clear view of what is covered, excluded, and overlooked.",
  },
  {
    icon: "📈",
    title: "Premium Forecasting",
    description: "See how today's policy may behave across future repricing cycles and age bands.",
  },
  {
    icon: "✓",
    title: "Rights & Overlap Intelligence",
    description: "Spot duplicated coverage and identify rights you can request under BNM guidance.",
  },
];

const steps = [
  {
    number: "01",
    title: "Upload Policies",
    description: "Drop in your PDFs. We extract coverage, premiums, and terms in seconds.",
  },
  {
    number: "02",
    title: "Review Signals",
    description: "Understand overlap, projected costs, and protections that apply to you.",
  },
  {
    number: "03",
    title: "Decide with Confidence",
    description: "Use the verdict, savings estimate, and source-backed reasoning to act.",
  },
];

// Dashboard preview mockup component
function DashboardPreview() {
  return (
    <div className="dashboard-preview panel">
      <div className="preview-header">
        <span className="preview-label">Analysis Example</span>
      </div>
      
      <div className="preview-grid">
        <div className="preview-card verdict-card">
          <div className="preview-label-small">Verdict</div>
          <div className="verdict-badge">Restructure</div>
          <div className="preview-value-small">Potential savings identified</div>
        </div>

        <div className="preview-card savings-card">
          <div className="preview-label-small">10-Yr Savings</div>
          <div className="savings-amount">RM 8,400</div>
          <div className="preview-value-small">vs. current trajectory</div>
        </div>

        <div className="preview-card overlap-card">
          <div className="preview-label-small">Overlap Coverage</div>
          <div className="overlap-badge">2 areas</div>
          <div className="preview-value-small">Possible consolidation</div>
        </div>

        <div className="preview-card confidence-card">
          <div className="preview-label-small">Confidence</div>
          <div className="confidence-meter">
            <div className="confidence-bar" style={{ width: '78%' }}></div>
          </div>
          <div className="preview-value-small">High confidence</div>
        </div>
      </div>

      <div className="preview-footer">
        <p className="preview-footer-text">All claims backed by policy source citations</p>
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <main className="page landing-page">
      {/* Two-Column Hero Section */}
      <section className="landing-hero-section">
        <div className="hero-left">
          <p className="eyebrow">PolicyClaw</p>
          <h1 className="hero-headline">Claw back what your insurer won&apos;t tell you.</h1>
          <p className="hero-subtitle">
            AI-powered clarity on your coverage. Spot overlaps. Forecast costs. Claim your rights. All backed by source citations.
          </p>
          
          <div className="hero-cta-group">
            <Link href="/analyze" className="cta-button cta-primary">
              Start Analysis
            </Link>
          </div>

          <p className="hero-trust-line">🔒 Your policies never leave your browser</p>
        </div>

        <div className="hero-right">
          <DashboardPreview />
        </div>
      </section>

      {/* Features Section */}
      <section className="landing-section features-section">
        <div className="section-label">Capabilities</div>
        <h2 className="section-title">Everything you need to review your coverage.</h2>
        
        <div className="feature-grid">
          {features.map((feature) => (
            <article className="feature-card" key={feature.title}>
              <div className="feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </article>
          ))}
        </div>
      </section>

      {/* How It Works Section */}
      <section className="landing-section workflow-section">
        <div className="section-label">Process</div>
        <h2 className="section-title">Three steps to clarity.</h2>
        
        <div className="steps-grid">
          {steps.map((step) => (
            <article className="step-card" key={step.number}>
              <div className="step-number">{step.number}</div>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </section>

      {/* Trust Section */}
      <section className="landing-section trust-section">
        <div className="section-label">Trust</div>
        <h2 className="section-title">Transparency at every step.</h2>
        
        <div className="trust-grid">
          <div className="trust-item">
            <div className="trust-icon">📋</div>
            <h3>Source-Backed Claims</h3>
            <p>Every insight references the exact policy section and page number.</p>
          </div>
          <div className="trust-item">
            <div className="trust-icon">⚖️</div>
            <h3>Your Decision, Supported</h3>
            <p>We analyze and explain. You decide. No automated recommendations imposed.</p>
          </div>
          <div className="trust-item">
            <div className="trust-icon">🇲🇾</div>
            <h3>Built for Malaysia</h3>
            <p>Designed with BNM guidance and Malaysian insurance realities in mind.</p>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="landing-final-cta">
        <h2>Ready to inspect your policies?</h2>
        <p>Upload your PDFs and get clarity in minutes. No credit card needed.</p>
        <Link href="/analyze" className="cta-button cta-primary">
          Start Analysis
        </Link>
      </section>
    </main>
  );
}
