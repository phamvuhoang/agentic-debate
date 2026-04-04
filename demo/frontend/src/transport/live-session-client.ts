import type { DebateEvent, SessionActionRequest } from './protocol';
import { parseDebateEvent } from './protocol';

export interface SessionUrls {
  session_id: string;
  events_url: string;
  actions_url: string;
  replay_url: string;
}

export class LiveSessionClient {
  async createSession(request: {
    topic: string;
    output_locale?: string;
    participant_count?: number | null;
    round_count?: number | null;
  }): Promise<SessionUrls> {
    // Strip null/undefined values so Pydantic uses defaults
    const body: Record<string, unknown> = { topic: request.topic };
    if (request.output_locale) body.output_locale = request.output_locale;
    if (request.participant_count != null) body.participant_count = request.participant_count;
    if (request.round_count != null) body.round_count = request.round_count;

    const response = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(`Failed to create session: ${response.status}`);
    return response.json() as Promise<SessionUrls>;
  }

  async connect(eventsUrl: string, onEvent: (event: DebateEvent) => void): Promise<void> {
    const source = new EventSource(eventsUrl);
    source.onmessage = (e) => {
      try {
        const raw = JSON.parse(e.data);
        onEvent(parseDebateEvent(raw));
      } catch {
        // skip malformed events
      }
    };
  }

  async sendAction(actionsUrl: string, action: SessionActionRequest): Promise<void> {
    await fetch(actionsUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(action),
    });
  }
}
