import type { DebateEvent } from '../transport/protocol';
import { createInitialSessionState, reduceEvent } from './event-reducer';
import type { SessionState } from './types';

type Listener = (state: SessionState) => void;

export interface Store {
  getState(): SessionState;
  dispatch(event: DebateEvent): void;
  dispatchSessionCreated(sessionId: string): void;
  subscribe(listener: Listener): () => void;
  reset(): void;
}

export function createStore(): Store {
  let state = createInitialSessionState();
  const listeners = new Set<Listener>();

  function notify() {
    for (const l of listeners) l(state);
  }

  return {
    getState: () => state,

    dispatch(event: DebateEvent) {
      state = reduceEvent(state, event);
      notify();
    },

    dispatchSessionCreated(sessionId: string) {
      state = { ...state, sessionId };
      notify();
    },

    subscribe(listener: Listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },

    reset() {
      state = createInitialSessionState();
      notify();
    },
  };
}
