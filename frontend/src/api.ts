export interface PersonFindRequest {
  company: string;
  designation: string;
}

export interface CandidateEvidence {
  first_name: string;
  last_name: string;
  title: string;
  company_guess?: string | null;
  source_url: string;
  source_label: string;
  query_variant?: string | null;
  credibility_score: number;
}

export interface PersonFindResponse {
  first_name: string;
  last_name: string;
  title: string;
  company: string;
  source_url: string;
  source_label: string;
  confidence: number;
  raw_candidates: CandidateEvidence[];
  agent_notes?: string | null;
}

export interface ErrorResponse {
  error: string;
  confidence: number;
  tried_sources?: string[];
  warning?: string;
  kind?: 'no_result' | 'upstream_error' | 'bad_request';
}

const API_BASE = 'http://localhost:8000';

export async function findPerson(
  payload: PersonFindRequest,
): Promise<PersonFindResponse | ErrorResponse> {
  const res = await fetch(`${API_BASE}/api/find-person`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    return {
      error: `HTTP ${res.status}: ${text}`,
      confidence: 0,
      kind: 'upstream_error',
    };
  }

  return res.json();
}

