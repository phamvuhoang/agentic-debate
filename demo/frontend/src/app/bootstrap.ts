import { detectPreferences, type AppEnvironment } from './preferences';
import { renderFallbackShell } from '../fallback/fallback-shell';
import { createStore } from '../state/store';
import { selectSceneView, selectOverlayView } from '../state/selectors';
import { LiveSessionClient } from '../transport/live-session-client';
import { ReplayClient } from '../transport/replay-client';
import { SessionController } from './session-controller';
import { renderPromptBar, type DebateConfig } from '../overlay/prompt-bar';
import { renderCaptionPanel, updateCaptionPanel } from '../overlay/caption-panel';
import { renderSpeakerBanner, updateSpeakerBanner } from '../overlay/speaker-banner';
import { renderParticipantPanel, updateParticipantPanel } from '../overlay/participant-panel';
import { renderStatusBar, updateStatusBar } from '../overlay/status-bar';
import { renderTranscriptPanel, createTranscriptToggle } from '../overlay/transcript-panel';

export interface BootstrapResult {
  mode: 'scene' | 'fallback';
}

export async function bootstrapApp(
  mount: HTMLElement,
  env: Partial<AppEnvironment> = {},
): Promise<BootstrapResult> {
  const preferences = detectPreferences(env);

  if (!preferences.hasWebGL) {
    renderFallbackShell(mount);
    return { mode: 'fallback' };
  }

  // Lazy import SceneRenderer to avoid WebGL init in tests/fallback path
  const { SceneRenderer } = await import('../scene/renderer');

  const store = createStore();
  const liveClient = new LiveSessionClient();
  const replayClient = new ReplayClient();
  const controller = new SessionController({ liveClient, replayClient, store });

  const sceneRenderer = new SceneRenderer(mount);

  // Status bar (top center) — shows topic, phase, round
  const statusBar = renderStatusBar();
  mount.append(statusBar);

  // Speaker banner (top left) — shows active speaker
  const speakerBanner = renderSpeakerBanner();
  mount.append(speakerBanner);

  // Participant panel (right sidebar) — shows all members
  const participantPanel = renderParticipantPanel();
  mount.append(participantPanel);

  // Caption panel (bottom center) — shows current argument or verdict
  const captionPanel = renderCaptionPanel({ text: null });
  mount.append(captionPanel);

  // Transcript panel (left sidebar) — scrollable full history + download
  const transcript = renderTranscriptPanel();
  mount.append(transcript.root);

  // Transcript toggle button (bottom right)
  const transcriptToggle = createTranscriptToggle(transcript);
  transcriptToggle.setAttribute('hidden', '');
  mount.append(transcriptToggle);

  // Prompt bar — created as a function so we can re-show after debate ends
  let activePromptBar: HTMLElement | null = null;

  function showPromptBar() {
    if (activePromptBar) return;
    activePromptBar = renderPromptBar({
      onSubmit: (config: DebateConfig) => {
        activePromptBar?.remove();
        activePromptBar = null;
        startNewDebate(config);
      },
    });
    mount.append(activePromptBar);
  }

  async function startNewDebate(config: DebateConfig) {
    store.reset();
    await controller.startDebate({
      topic: config.topic,
      outputLocale: config.outputLocale,
      participantCount: config.participantCount,
      roundCount: config.roundCount,
    });
  }

  showPromptBar();

  let prevPhase = 'idle';

  store.subscribe((state) => {
    sceneRenderer.render(selectSceneView(state));
    const view = selectOverlayView(state);

    updateStatusBar(statusBar, view);
    updateSpeakerBanner(speakerBanner, view.activeSpeaker);
    updateParticipantPanel(participantPanel, view.participants, state.activeSpeakerId);
    updateCaptionPanel(captionPanel, {
      phase: view.phase,
      currentCaption: view.currentCaption,
      verdict: view.verdict,
      activeSpeakerLabel: view.activeSpeaker?.label,
    });
    transcript.update(view.captions, view.verdict, view.currentRound);

    // Show transcript toggle once debate has content
    if (view.captions.length > 0 || view.verdict) {
      transcriptToggle.removeAttribute('hidden');
    } else {
      transcriptToggle.setAttribute('hidden', '');
    }

    // Re-show prompt bar when debate ends (complete or error)
    if (
      (view.phase === 'complete' || view.phase === 'error') &&
      prevPhase !== 'complete' &&
      prevPhase !== 'error' &&
      prevPhase !== 'idle'
    ) {
      showPromptBar();
    }

    prevPhase = view.phase;
  });

  return { mode: 'scene' };
}
