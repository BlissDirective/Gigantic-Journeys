using System;
using System.Collections.Generic;

namespace GiganticJourneys.Capture
{
    /// <summary>Where the capture flow is (SPEC §3.1; capture-ux-coaching-v1 §1, §5).</summary>
    public enum CaptureState
    {
        /// <summary>ARKit is finding the space; recording unlocks once tracking is normal.</summary>
        Framing,

        /// <summary>Coached capture.</summary>
        Recording,

        /// <summary>Tracking lost: coaching paused, "Point at a spot you've already scanned".</summary>
        Relocalizing,

        /// <summary>A call or app switch paused the session: Resume or Start over.</summary>
        Interrupted,

        /// <summary>Done tapped with unpainted regions: the arrow, Got it or Upload anyway.</summary>
        MissedCornerCheck,

        /// <summary>The readiness gate: one kind line, Upload anyway, or Retake.</summary>
        QualityGate,

        /// <summary>The last 5 s with Retake.</summary>
        Preview,

        /// <summary>Confirmed: strip + bundle, then upload.</summary>
        Confirmed,
    }

    /// <summary>A cue for the capture UI (a haptic, a card, a line of copy).</summary>
    public enum CaptureCueKind
    {
        /// <summary>The speed arc turned amber: one gentle haptic.</summary>
        SpeedHaptic,

        /// <summary>"Slow down a little" after a full second of amber.</summary>
        SlowDown,

        /// <summary>A blurred frame: one soft haptic tick and an amber edge pulse, no words.</summary>
        BlurTick,

        /// <summary>The low-light card, once per session.</summary>
        TooDark,

        /// <summary>Tracking lost: pause coaching and ask to relocalize.</summary>
        Relocalize,

        /// <summary>Tracking back: coaching resumes with coverage intact.</summary>
        Relocalized,

        /// <summary>Done unlocked (60 % coverage or 60 s).</summary>
        DoneAvailable,

        /// <summary>The ring turned amber past three minutes.</summary>
        LongCapture,

        /// <summary>The one-time richer first-run coach-through (SPEC §3.1).</summary>
        FirstRunCoachThrough,
    }

    /// <summary>
    /// The capture flow's state machine and live coaching, platform-neutral (M1-CAPT-01). The AR
    /// adapter feeds frames; the UI reads the state and drains cues. Every state has a way back, the
    /// gate never hard-stops, and nothing here throws on a user action at the wrong time (it returns
    /// false instead), so a stray tap cannot crash the capture.
    /// </summary>
    public sealed class CaptureSession
    {
        private readonly List<CaptureCueKind> _cues = new List<CaptureCueKind>();
        private readonly List<CaptureFrame> _frames = new List<CaptureFrame>();
        private readonly List<bool> _accepted = new List<bool>();
        private readonly List<CapturePass> _passes = new List<CapturePass>();
        private readonly bool _firstRun;
        private SpeedMeter _speed;
        private BlurGate _blur;
        private LightMeter _light;
        private CoverageMap _coverage;
        private ParallaxMeter _parallax;
        private TrackingMeter _tracking;
        private bool _trackingReady;
        private bool _doneAnnounced;
        private bool _longAnnounced;
        private bool _firstRunShown;
        private bool _newPassPending;
        private string _pendingPassReason = CapturePass.Start;
        private double _activeSeconds;
        private double _lastFrameTime = -1;

        /// <summary>Starts a session in Framing with the mode already chosen on the toggle.</summary>
        public CaptureSession(CaptureMode mode, bool firstRun)
        {
            Mode = mode;
            _firstRun = firstRun;
            ResetMeasurements();
        }

        /// <summary>A free retry after a downstream reconstruction failure: same mode, a kind line, back to Framing.</summary>
        public static CaptureSession RetryAfterReconstructionFailure(CaptureMode previousMode) =>
            new CaptureSession(previousMode, firstRun: false)
            {
                RetryMessage = CoachingCopy.ReconstructionFailed,
            };

        /// <summary>The capture mode (fixed for the session; Start over keeps it).</summary>
        public CaptureMode Mode { get; }

        /// <summary>Set when this session is a free retry (shown once on entry).</summary>
        public string RetryMessage { get; private set; }

        /// <summary>The current state.</summary>
        public CaptureState State { get; private set; } = CaptureState.Framing;

        /// <summary>True when the record button can start recording (Framing with tracking found).</summary>
        public bool CanStartRecording => State == CaptureState.Framing && _trackingReady;

        /// <summary>Active recording time (s), interruptions and relocalization excluded.</summary>
        public float ActiveSeconds => (float)_activeSeconds;

        /// <summary>The progress ring, 0–1 over the 90 s target (a target, not a limit).</summary>
        public float RingProgress =>
            Math.Min(1f, ActiveSeconds / CaptureTuning.Timing.RingTargetSec);

        /// <summary>True past three minutes (ring amber, "Long captures rebuild worse").</summary>
        public bool RingAmber => ActiveSeconds > CaptureTuning.Timing.LongCaptureSec;

        /// <summary>True once Done is available (60 % coverage or 60 s).</summary>
        public bool DoneAvailable =>
            _coverage.Fraction >= CaptureTuning.Timing.DoneCoverage
            || ActiveSeconds >= CaptureTuning.Timing.DoneSec;

        /// <summary>The live coverage map.</summary>
        public CoverageMap Coverage => _coverage;

        /// <summary>The live speed meter (the arc).</summary>
        public SpeedMeter Speed => _speed;

        /// <summary>The blur gate (accepted/rejected counts).</summary>
        public BlurGate Blur => _blur;

        /// <summary>The light meter.</summary>
        public LightMeter Light => _light;

        /// <summary>Tracking continuity.</summary>
        public TrackingMeter Tracking => _tracking;

        /// <summary>Recorded frames, in order.</summary>
        public IReadOnlyList<CaptureFrame> Frames => _frames;

        /// <summary>Whether each recorded frame passed the blur gate.</summary>
        public IReadOnlyList<bool> Accepted => _accepted;

        /// <summary>Recording passes (start, resume, relocalized).</summary>
        public IReadOnlyList<CapturePass> Passes => _passes;

        /// <summary>The readiness score over everything recorded so far.</summary>
        public ReadinessScore Readiness =>
            new ReadinessScore(
                _coverage.Fraction,
                _parallax.Score,
                _blur.AcceptedRatio,
                _light.Score,
                _tracking.NormalFraction,
                ActiveSeconds
            );

        /// <summary>The gate's one kind line (null when the scan looks ready).</summary>
        public string GateMessage => CoachingCopy.ForWeakness(Readiness.Weakest, Mode);

        /// <summary>Returns and clears the cues raised since the last call.</summary>
        public IReadOnlyList<CaptureCueKind> DrainCues()
        {
            var copy = _cues.ToArray();
            _cues.Clear();
            return copy;
        }

        /// <summary>Framing: the AR adapter reports the tracking state until recording starts.</summary>
        public void ReportFramingTracking(TrackingQuality tracking)
        {
            if (State == CaptureState.Framing)
            {
                _trackingReady = tracking == TrackingQuality.Normal;
            }
        }

        /// <summary>The record button. False unless tracking has found the space.</summary>
        public bool StartRecording()
        {
            if (!CanStartRecording)
            {
                return false;
            }

            State = CaptureState.Recording;
            _newPassPending = true;
            _pendingPassReason = CapturePass.Start;
            if (_firstRun && !_firstRunShown)
            {
                _firstRunShown = true;
                _cues.Add(CaptureCueKind.FirstRunCoachThrough);
            }

            return true;
        }

        /// <summary>Feeds one recorded frame (Recording or Relocalizing; ignored otherwise).</summary>
        public void AddFrame(in CaptureFrame frame)
        {
            if (State != CaptureState.Recording && State != CaptureState.Relocalizing)
            {
                return;
            }

            if (_frames.Count > 0 && frame.Index <= _frames[_frames.Count - 1].Index)
            {
                return; // duplicate or out-of-order frame from the platform layer
            }

            if (
                _lastFrameTime >= 0
                && frame.Time > _lastFrameTime
                && State == CaptureState.Recording
            )
            {
                _activeSeconds += frame.Time - _lastFrameTime;
            }

            _lastFrameTime = frame.Time;
            if (_newPassPending && _passes.Count < CapturePass.MaxPasses)
            {
                _passes.Add(new CapturePass(frame.Index, frame.Index, _pendingPassReason));
                _newPassPending = false;
            }
            else
            {
                // Past the bundle's pass limit a break extends the last pass instead of starting one.
                _newPassPending = false;
                var last = _passes[_passes.Count - 1];
                _passes[_passes.Count - 1] = new CapturePass(
                    last.FirstFrame,
                    frame.Index,
                    last.Reason
                );
            }

            _tracking.Add(frame);
            _light.Add(frame);
            if (_light.ShowCardThisFrame)
            {
                _cues.Add(CaptureCueKind.TooDark);
            }

            bool tracked = frame.Tracking == TrackingQuality.Normal;
            bool sharp = _blur.Accept(frame.Sharpness);
            _frames.Add(frame);
            _accepted.Add(sharp);

            if (State == CaptureState.Recording && _tracking.NeedsRelocalize)
            {
                State = CaptureState.Relocalizing;
                _speed.Reset();
                _cues.Add(CaptureCueKind.Relocalize);
                return;
            }

            if (State == CaptureState.Relocalizing)
            {
                if (!tracked)
                {
                    return;
                }

                // Relocalized: resume coaching with coverage intact; a new pass marks the break.
                State = CaptureState.Recording;
                _cues.Add(CaptureCueKind.Relocalized);
                var last = _passes[_passes.Count - 1];
                if (last.FirstFrame < frame.Index && _passes.Count < CapturePass.MaxPasses)
                {
                    _passes[_passes.Count - 1] = new CapturePass(
                        last.FirstFrame,
                        _frames[_frames.Count - 2].Index,
                        last.Reason
                    );
                    _passes.Add(new CapturePass(frame.Index, frame.Index, CapturePass.Relocalized));
                }
            }

            if (!tracked)
            {
                return;
            }

            if (!sharp)
            {
                _cues.Add(CaptureCueKind.BlurTick);
            }
            else
            {
                _coverage.Add(frame);
                _parallax.Add(frame.Position);
            }

            _speed.Add(frame);
            if (_speed.HapticThisFrame)
            {
                _cues.Add(CaptureCueKind.SpeedHaptic);
            }

            if (_speed.ShowSlowDownHint)
            {
                _cues.Add(CaptureCueKind.SlowDown);
            }

            if (!_doneAnnounced && DoneAvailable)
            {
                _doneAnnounced = true;
                _cues.Add(CaptureCueKind.DoneAvailable);
            }

            if (!_longAnnounced && RingAmber)
            {
                _longAnnounced = true;
                _cues.Add(CaptureCueKind.LongCapture);
            }
        }

        /// <summary>A call or app switch. The session is preserved.</summary>
        public bool Interrupt()
        {
            if (State != CaptureState.Recording && State != CaptureState.Relocalizing)
            {
                return false;
            }

            State = CaptureState.Interrupted;
            return true;
        }

        /// <summary>Resume after an interruption: coverage kept, a new pass starts.</summary>
        public bool Resume()
        {
            if (State != CaptureState.Interrupted)
            {
                return false;
            }

            State = CaptureState.Recording;
            _speed.Reset();
            _lastFrameTime = -1; // the pause is not active time
            _newPassPending = true;
            _pendingPassReason = CapturePass.Resume;
            return true;
        }

        /// <summary>Start over (from an interruption, the gate or the preview): same mode, everything cleared.</summary>
        public bool StartOver()
        {
            if (
                State != CaptureState.Interrupted
                && State != CaptureState.QualityGate
                && State != CaptureState.Preview
                && State != CaptureState.MissedCornerCheck
            )
            {
                return false;
            }

            ResetMeasurements();
            State = CaptureState.Framing;
            return true;
        }

        /// <summary>Retake: the same as Start over, named as in the gate and the preview.</summary>
        public bool Retake() => StartOver();

        /// <summary>Done. Goes to the missed-corner check when something is unpainted, else to the gate.</summary>
        public bool Finish()
        {
            if (State != CaptureState.Recording || !DoneAvailable)
            {
                return false;
            }

            State = _coverage.TryGetMissedCorner(out _, out _)
                ? CaptureState.MissedCornerCheck
                : CaptureState.QualityGate;
            return true;
        }

        /// <summary>Got it at the missed-corner arrow: keep recording (same pass, the arrow stays in view).</summary>
        public bool KeepRecording()
        {
            if (State != CaptureState.MissedCornerCheck)
            {
                return false;
            }

            State = CaptureState.Recording;
            _lastFrameTime = -1;
            return true;
        }

        /// <summary>Upload anyway (missed-corner check or gate): always available, never blocked by the score.</summary>
        public bool UploadAnyway()
        {
            if (State == CaptureState.MissedCornerCheck)
            {
                State = CaptureState.QualityGate;
                return true;
            }

            if (State == CaptureState.QualityGate)
            {
                State = CaptureState.Preview;
                return true;
            }

            return false;
        }

        /// <summary>Confirm on the preview: hand over to strip + bundle.</summary>
        public bool Confirm()
        {
            if (State != CaptureState.Preview)
            {
                return false;
            }

            State = CaptureState.Confirmed;
            return true;
        }

        private void ResetMeasurements()
        {
            _speed = new SpeedMeter(Mode);
            _blur = new BlurGate();
            _light = new LightMeter();
            _coverage = new CoverageMap(Mode);
            _parallax = new ParallaxMeter(Mode);
            _tracking = new TrackingMeter();
            _frames.Clear();
            _accepted.Clear();
            _passes.Clear();
            _cues.Clear();
            _trackingReady = false;
            _doneAnnounced = false;
            _longAnnounced = false;
            _activeSeconds = 0;
            _lastFrameTime = -1;
            _newPassPending = false;
        }
    }

    /// <summary>A contiguous recording pass (frame indices inclusive).</summary>
    public readonly struct CapturePass
    {
        /// <summary>First pass of a capture.</summary>
        public const string Start = "start";

        /// <summary>After an interruption.</summary>
        public const string Resume = "resume";

        /// <summary>After tracking loss.</summary>
        public const string Relocalized = "relocalized";

        /// <summary>The bundle records at most this many passes (capture_bundle.schema.json).</summary>
        public const int MaxPasses = 6;

        /// <summary>First frame index.</summary>
        public readonly int FirstFrame;

        /// <summary>Last frame index.</summary>
        public readonly int LastFrame;

        /// <summary>Why the pass started ("start", "resume", "relocalized"; "add-pass" is M1-CAPT-04).</summary>
        public readonly string Reason;

        /// <summary>Creates a pass.</summary>
        public CapturePass(int firstFrame, int lastFrame, string reason)
        {
            FirstFrame = firstFrame;
            LastFrame = lastFrame;
            Reason = reason;
        }
    }
}
