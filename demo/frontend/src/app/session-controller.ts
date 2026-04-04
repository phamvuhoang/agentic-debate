import type { LiveSessionClient, SessionUrls } from '../transport/live-session-client';
import type { ReplayClient } from '../transport/replay-client';
import type { Store } from '../state/store';
import type { SessionActionRequest } from '../transport/protocol';

export interface StartDebateOptions {
  topic: string;
  outputLocale?: string;
  participantCount?: number | null;
  roundCount?: number | null;
}

interface SessionControllerOptions {
  liveClient: LiveSessionClient;
  replayClient: ReplayClient;
  store: Store;
}

export class SessionController {
  private readonly liveClient: LiveSessionClient;
  private readonly replayClient: ReplayClient;
  private readonly store: Store;
  private session: SessionUrls | null = null;

  constructor(options: SessionControllerOptions) {
    this.liveClient = options.liveClient;
    this.replayClient = options.replayClient;
    this.store = options.store;
  }

  async startDebate(options: StartDebateOptions): Promise<void> {
    const session = await this.liveClient.createSession({
      topic: options.topic,
      output_locale: options.outputLocale ?? 'en',
      participant_count: options.participantCount,
      round_count: options.roundCount,
    });
    this.session = session;
    this.store.dispatchSessionCreated(session.session_id);

    // Hydrate replay (events that already happened before SSE connection)
    try {
      const replay = await this.replayClient.fetchReplay(session.replay_url);
      for (const event of replay.events) {
        this.store.dispatch(event);
      }
    } catch {
      // replay unavailable — proceed live
    }

    // Connect live stream
    await this.liveClient.connect(session.events_url, (event) => {
      this.store.dispatch(event);
    });
  }

  async sendAction(action: SessionActionRequest): Promise<void> {
    if (!this.session) throw new Error('No active session');
    await this.liveClient.sendAction(this.session.actions_url, action);
  }
}
