import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Forensic video transport — forward via HTML5 video; reverse via server frame steps (R-165).
 */
export function useForensicPlayback({
  enabled,
  videoRef,
  fps = 30,
  stepFrame,
  getCurrentTime,
}) {
  const [direction, setDirection] = useState(null);
  const [speed, setSpeed] = useState(1);
  const directionRef = useRef(null);
  const speedRef = useRef(speed);
  const stepFrameRef = useRef(stepFrame);
  const reverseGenRef = useRef(0);

  stepFrameRef.current = stepFrame;
  speedRef.current = speed;

  const pause = useCallback(() => {
    reverseGenRef.current += 1;
    directionRef.current = null;
    setDirection(null);
    const v = videoRef?.current;
    if (v && !v.paused) v.pause();
  }, [videoRef]);

  const syncVideoToForensicTime = useCallback(() => {
    const v = videoRef?.current;
    const t = getCurrentTime?.() ?? 0;
    if (v && Number.isFinite(t) && Math.abs(v.currentTime - t) > 0.05) {
      try {
        v.currentTime = t;
      } catch {
        /* seekable range */
      }
    }
  }, [getCurrentTime, videoRef]);

  const playForward = useCallback(() => {
    if (!enabled) return;
    pause();
    directionRef.current = 'forward';
    setDirection('forward');
    syncVideoToForensicTime();
    const v = videoRef?.current;
    if (v) {
      v.playbackRate = Math.max(0.25, Math.min(4, speedRef.current));
      v.play().catch(() => {});
    }
  }, [enabled, pause, syncVideoToForensicTime, videoRef]);

  const playReverse = useCallback(() => {
    if (!enabled || !stepFrameRef.current) return;

    const t0 = getCurrentTime?.() ?? 0;
    if (t0 <= 0.001) return;

    const v = videoRef?.current;
    if (v) v.pause();

    reverseGenRef.current += 1;
    const gen = reverseGenRef.current;
    directionRef.current = 'reverse';
    setDirection('reverse');
    syncVideoToForensicTime();

    const runLoop = async () => {
      while (directionRef.current === 'reverse' && reverseGenRef.current === gen) {
        const t = getCurrentTime?.() ?? 0;
        if (t <= 0.001) break;

        try {
          await stepFrameRef.current(-1);
        } catch {
          break;
        }

        syncVideoToForensicTime();

        const rate = Math.max(0.25, Math.min(4, speedRef.current));
        const delayMs = Math.max(40, 1000 / (Math.max(1, fps) * rate));
        await new Promise((resolve) => {
          setTimeout(resolve, delayMs);
        });
      }

      if (reverseGenRef.current === gen) pause();
    };

    runLoop();
  }, [enabled, fps, getCurrentTime, pause, syncVideoToForensicTime, videoRef]);

  useEffect(() => {
    const v = videoRef?.current;
    if (!v) return undefined;
    const onEnded = () => {
      if (directionRef.current === 'forward') pause();
    };
    v.addEventListener('ended', onEnded);
    return () => v.removeEventListener('ended', onEnded);
  }, [pause, videoRef, direction]);

  useEffect(() => {
    if (direction === 'forward' && videoRef?.current) {
      videoRef.current.playbackRate = Math.max(0.25, Math.min(4, speed));
    }
    if (direction === 'reverse') {
      playReverse();
    }
  }, [speed]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!enabled) pause();
  }, [enabled, pause]);

  return {
    direction,
    isPlaying: direction != null,
    speed,
    setSpeed,
    playForward,
    playReverse,
    pause,
    toggleForward: () => (direction === 'forward' ? pause() : playForward()),
    toggleReverse: () => (direction === 'reverse' ? pause() : playReverse()),
  };
}
