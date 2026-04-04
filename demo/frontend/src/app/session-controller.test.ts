import { describe, expect, it } from 'vitest';
import { SessionController } from './session-controller';
import { createStore } from '../state/store';

describe('SessionController', () => {
  it('creates a session and subscribes to the event stream', async () => {
    const store = createStore();

    const fakeSession = {
      session_id: 'session-1',
      events_url: '/api/sessions/session-1/events',
      actions_url: '/api/sessions/session-1/actions',
      replay_url: '/api/sessions/session-1/replay',
    };

    class FakeLiveSessionClient {
      async createSession(_req: { topic: string }) {
        return fakeSession;
      }
      async connect(_url: string, _onEvent: (e: unknown) => void) {
        // no-op
      }
      async sendAction(_sessionId: string, _action: unknown) {}
    }

    class FakeReplayClient {
      async fetchReplay(_url: string) {
        return { session_id: 'session-1', events: [] };
      }
    }

    const controller = new SessionController({
      liveClient: new FakeLiveSessionClient() as any,
      replayClient: new FakeReplayClient() as any,
      store,
    });

    await controller.startDebate({ topic: 'Should AI replace doctors?' });

    expect(store.getState().sessionId).toBe('session-1');
  });
});
