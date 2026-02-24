import { FormEvent, useState } from 'react';
import './App.css';
import { ErrorResponse, PersonFindResponse, findPerson } from './api';

type ApiResult = PersonFindResponse | ErrorResponse | null;

function isError(result: ApiResult): result is ErrorResponse {
  return !!result && 'error' in result;
}

function App() {
  const [company, setCompany] = useState('Meta');
  const [designation, setDesignation] = useState('CEO');
  const [result, setResult] = useState<ApiResult>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const data = await findPerson({ company, designation });
      setResult(data);
    } catch (err: any) {
      setResult({
        error: err?.message ?? 'Unexpected error',
        confidence: 0,
        kind: 'upstream_error',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-root">
      <header className="app-header">
        <h1>Person Finder Tool</h1>
        <p>Discover key people by company and designation using public web intelligence.</p>
      </header>

      <main className="app-main">
        <section className="card form-card">
          <form onSubmit={handleSubmit} className="form">
            <label className="field">
              <span>Company</span>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g., Meta, Stripe, OpenAI"
                required
              />
            </label>

            <label className="field">
              <span>Designation</span>
              <input
                type="text"
                value={designation}
                onChange={(e) => setDesignation(e.target.value)}
                placeholder="e.g., CEO, CTO, Chief Marketing Officer"
                required
              />
            </label>

            <button type="submit" disabled={loading}>
              {loading ? 'Searching…' : 'Find Person'}
            </button>
          </form>
        </section>

        <section className="card result-card">
          {!result && !loading && <p>Enter a company and designation, then hit “Find Person”.</p>}

          {loading && <p>Running multi-source search and extraction…</p>}

          {result && isError(result) && (
            <div className="error">
              <h2>No confident match</h2>
              <p>{result.error}</p>
              {result.tried_sources && result.tried_sources.length > 0 && (
                <p className="meta">
                  Tried search variants: {result.tried_sources.join(', ')}
                </p>
              )}
            </div>
          )}

          {result && !isError(result) && (
            <div className="success">
              <h2>
                {result.first_name} {result.last_name}
              </h2>
              <p className="title-line">
                <strong>{result.title}</strong> @ <strong>{result.company}</strong>
              </p>
              <p className="meta">
                Confidence: {(result.confidence * 100).toFixed(0)}% · Source:{' '}
                <a href={result.source_url} target="_blank" rel="noreferrer">
                  {result.source_label}
                </a>
              </p>
              {result.agent_notes && <p className="meta">Agent notes: {result.agent_notes}</p>}

              {result.raw_candidates && result.raw_candidates.length > 0 && (
                <>
                  <h3>Supporting evidence</h3>
                  <div className="candidate-list">
                    {result.raw_candidates.slice(0, 5).map((c, idx) => (
                      <div key={idx} className="candidate">
                        <div>
                          <strong>
                            {c.first_name} {c.last_name}
                          </strong>{' '}
                          — {c.title}
                        </div>
                        <div className="meta">
                          {c.company_guess && <span>{c.company_guess} · </span>}
                          <span>
                            {(c.credibility_score * 100).toFixed(0)}% credibility ·{' '}
                            {c.query_variant && <>{c.query_variant} · </>}
                            <a href={c.source_url} target="_blank" rel="noreferrer">
                              {c.source_label}
                            </a>
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
