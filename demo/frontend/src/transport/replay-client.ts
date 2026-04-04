import type { DebateEvent } from './protocol';
import { parseDebateEvent } from './protocol';

export interface ReplayResponse {
  session_id: string;
  events: DebateEvent[];
}

export class ReplayClient {
  async fetchReplay(replayUrl: string): Promise<ReplayResponse> {
    const response = await fetch(replayUrl);
    if (!response.ok) throw new Error(`Failed to fetch replay: ${response.status}`);
    const data = await response.json() as { session_id: string; events: unknown[] };
    return {
      session_id: data.session_id,
      events: data.events.map(parseDebateEvent),
    };
  }
}
