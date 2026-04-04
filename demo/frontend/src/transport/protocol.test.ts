import { describe, expect, it } from 'vitest';
import { parseDebateEvent } from './protocol';

describe('parseDebateEvent', () => {
  it('accepts supported typed events', () => {
    const event = parseDebateEvent({
      session_id: 'session-1',
      sequence: 1,
      type: 'speaker_activated',
      phase: 'debate',
      payload: { speaker_id: 'economist' },
    });

    expect(event.type).toBe('speaker_activated');
  });

  it('throws on unknown event type', () => {
    expect(() =>
      parseDebateEvent({
        session_id: 'session-1',
        sequence: 1,
        type: 'banana' as any,
        phase: 'debate',
        payload: {},
      })
    ).toThrow();
  });
});
