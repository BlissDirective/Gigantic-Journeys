using System.Collections.Generic;
using System.Linq;
using GiganticJourneys.Capture;
using NUnit.Framework;
using UnityEngine;

namespace GiganticJourneys.Tests.Capture
{
    /// <summary>M1-CAPT-01 AT-2/AT-3/AT-6: the capture flow, the quality gate, failure and recovery.</summary>
    public class CaptureSessionTests
    {
        internal static CaptureSession Recording(CaptureMode mode, bool firstRun = false)
        {
            var session = new CaptureSession(mode, firstRun);
            session.ReportFramingTracking(TrackingQuality.Normal);
            Assert.That(session.StartRecording(), Is.True);
            return session;
        }

        internal static List<CaptureCueKind> Feed(
            CaptureSession session,
            IEnumerable<CaptureFrame> frames
        )
        {
            var cues = new List<CaptureCueKind>();
            foreach (var f in frames)
            {
                session.AddFrame(f);
                cues.AddRange(session.DrainCues());
            }

            return cues;
        }

        [Test]
        public void RecordingWaitsForTracking()
        {
            var session = new CaptureSession(CaptureMode.Room, firstRun: false);
            Assert.That(session.State, Is.EqualTo(CaptureState.Framing));
            Assert.That(session.StartRecording(), Is.False);
            session.ReportFramingTracking(TrackingQuality.Limited);
            Assert.That(session.CanStartRecording, Is.False);
            session.ReportFramingTracking(TrackingQuality.Normal);
            Assert.That(session.StartRecording(), Is.True);
            Assert.That(session.State, Is.EqualTo(CaptureState.Recording));
        }

        [Test]
        public void GoodRoomCapture_UnlocksDoneAndLooksReady()
        {
            var session = Recording(CaptureMode.Room);
            var cues = Feed(session, new SyntheticCapture().Generate(CaptureMode.Room));

            Assert.That(cues, Has.Member(CaptureCueKind.DoneAvailable));
            Assert.That(cues, Has.No.Member(CaptureCueKind.SpeedHaptic));
            Assert.That(cues, Has.No.Member(CaptureCueKind.BlurTick));
            Assert.That(cues, Has.No.Member(CaptureCueKind.TooDark));
            Assert.That(session.ActiveSeconds, Is.EqualTo(75f).Within(0.1f));
            Assert.That(session.RingProgress, Is.EqualTo(75f / 90f).Within(0.01f));
            var readiness = session.Readiness;
            Assert.That(readiness.Score, Is.GreaterThan(0.9f));
            Assert.That(readiness.Weakest, Is.EqualTo(ReadinessWeakness.None));
            Assert.That(session.GateMessage, Is.Null);
        }

        [Test]
        public void GoodTabletopCapture_LooksReady()
        {
            var session = Recording(CaptureMode.Tabletop);
            Feed(session, new SyntheticCapture().Generate(CaptureMode.Tabletop));
            Assert.That(session.Coverage.Fraction, Is.EqualTo(1f));
            Assert.That(session.Readiness.Weakest, Is.EqualTo(ReadinessWeakness.None));
        }

        [Test]
        public void DoneAt60Seconds_EvenWithLowCoverage()
        {
            var session = Recording(CaptureMode.Room);
            // standing still, looking one way: coverage stays tiny
            var frames = Enumerable
                .Range(0, 61 * 30)
                .Select(i => new CaptureFrame(
                    i,
                    i / 30.0,
                    new Vector3(0f, 1.4f, 0f),
                    Quaternion.identity,
                    TrackingQuality.Normal,
                    150f,
                    0.5f,
                    false
                ));
            Feed(session, frames.Take(59 * 30));
            Assert.That(session.DoneAvailable, Is.False);
            Assert.That(session.Finish(), Is.False, "Done is not offered yet");
            Feed(session, frames.Skip(59 * 30));
            Assert.That(session.DoneAvailable, Is.True);
        }

        [Test]
        public void Finish_WithGapsGoesThroughTheMissedCornerCheck_AndUploadAnywayIsAlwaysThere()
        {
            var session = Recording(CaptureMode.Room);
            Feed(session, new SyntheticCapture { SweepFraction = 0.5f }.Generate(CaptureMode.Room));
            Assert.That(session.DoneAvailable, Is.True);
            Assert.That(session.Finish(), Is.True);
            Assert.That(session.State, Is.EqualTo(CaptureState.MissedCornerCheck));

            Assert.That(session.KeepRecording(), Is.True, "Got it keeps recording");
            Assert.That(session.State, Is.EqualTo(CaptureState.Recording));
            Assert.That(session.Finish(), Is.True);

            Assert.That(session.UploadAnyway(), Is.True);
            Assert.That(session.State, Is.EqualTo(CaptureState.QualityGate));
            Assert.That(session.GateMessage, Is.Not.Null, "a weak scan gets one kind line");
            Assert.That(session.UploadAnyway(), Is.True, "the gate never hard-stops");
            Assert.That(session.State, Is.EqualTo(CaptureState.Preview));
            Assert.That(session.Confirm(), Is.True);
            Assert.That(session.State, Is.EqualTo(CaptureState.Confirmed));
        }

        [Test]
        public void DarkCapture_ShowsTheCardOnce_AndTheGateSaysTurnOnALamp()
        {
            var session = Recording(CaptureMode.Room);
            var synth = new SyntheticCapture { DarkWindow = new Vector2(0f, 75f) };
            var cues = Feed(session, synth.Generate(CaptureMode.Room));
            Assert.That(cues.Count(c => c == CaptureCueKind.TooDark), Is.EqualTo(1));
            Assert.That(session.Readiness.Weakest, Is.EqualTo(ReadinessWeakness.Light));
            Assert.That(session.GateMessage, Is.EqualTo(CoachingCopy.TooDark));
        }

        [Test]
        public void BlurBurst_TicksAndIsExcludedFromCoverage()
        {
            var session = Recording(CaptureMode.Room);
            var synth = new SyntheticCapture { BlurWindow = new Vector2(10f, 40f) };
            var cues = Feed(session, synth.Generate(CaptureMode.Room));
            Assert.That(cues, Has.Member(CaptureCueKind.BlurTick));
            Assert.That(session.Blur.Rejected, Is.EqualTo(30 * 30));
            Assert.That(session.Readiness.Sharpness, Is.EqualTo(1f - 30f / 75f).Within(0.01f));

            var clean = Recording(CaptureMode.Room);
            Feed(clean, new SyntheticCapture().Generate(CaptureMode.Room));
            Assert.That(
                session.Coverage.Fraction,
                Is.LessThan(clean.Coverage.Fraction),
                "blurred frames paint nothing"
            );
        }

        [Test]
        public void ShakyCapture_GateCoachesSlowingDown()
        {
            var session = Recording(CaptureMode.Room);
            Feed(session, new SyntheticCapture { BlurEveryNth = 2 }.Generate(CaptureMode.Room));
            // the first shaky frame arrives before the median has three samples, so 1 of 1125 slips through
            Assert.That(session.Blur.Rejected, Is.EqualTo(1124));
            Assert.That(session.Readiness.Sharpness, Is.EqualTo(0.5f).Within(0.001f));
            Assert.That(session.Readiness.Weakest, Is.EqualTo(ReadinessWeakness.Sharpness));
            Assert.That(session.GateMessage, Is.EqualTo(CoachingCopy.SlowDown));
        }

        [Test]
        public void TooFast_HapticThenSlowDownHint()
        {
            var session = Recording(CaptureMode.Tabletop);
            var synth = new SyntheticCapture { SpeedFactor = 12f };
            var cues = Feed(session, synth.Generate(CaptureMode.Tabletop));
            Assert.That(cues, Has.Member(CaptureCueKind.SpeedHaptic));
            Assert.That(cues, Has.Member(CaptureCueKind.SlowDown));
        }

        [Test]
        public void TrackingLoss_RelocalizesAndKeepsCoverage()
        {
            var session = Recording(CaptureMode.Room);
            var synth = new SyntheticCapture { TrackingLossWindow = new Vector2(20f, 23f) };
            var frames = synth.Generate(CaptureMode.Room);
            Feed(session, frames.Take(20 * 30));
            float before = session.Coverage.Fraction;
            var cues = Feed(session, frames.Skip(20 * 30).Take(2 * 30));
            Assert.That(session.State, Is.EqualTo(CaptureState.Relocalizing));
            Assert.That(cues, Has.Member(CaptureCueKind.Relocalize));
            Assert.That(
                session.Coverage.Fraction,
                Is.EqualTo(before),
                "progress is never discarded or painted while lost"
            );
            cues = Feed(session, frames.Skip(22 * 30));
            Assert.That(cues, Has.Member(CaptureCueKind.Relocalized));
            Assert.That(session.State, Is.EqualTo(CaptureState.Recording));
            Assert.That(session.Coverage.Fraction, Is.GreaterThan(before));
            Assert.That(
                session.Passes.Select(p => p.Reason),
                Is.EqualTo(new[] { "start", "relocalized" })
            );
            Assert.That(session.Passes[1].FirstFrame, Is.EqualTo(session.Passes[0].LastFrame + 1));
            Assert.That(
                session.ActiveSeconds,
                Is.LessThan(75f - 2f),
                "time spent relocalizing is not active time"
            );
        }

        [Test]
        public void Interruption_OffersResumeOrStartOver()
        {
            var session = Recording(CaptureMode.Room);
            var frames = new SyntheticCapture().Generate(CaptureMode.Room);
            Feed(session, frames.Take(300));
            Assert.That(session.Interrupt(), Is.True);
            Assert.That(session.State, Is.EqualTo(CaptureState.Interrupted));
            // frames during the interruption are ignored
            Feed(session, frames.Skip(300).Take(100));
            Assert.That(session.Frames.Count, Is.EqualTo(300));
            float before = session.Coverage.Fraction;

            Assert.That(session.Resume(), Is.True);
            Feed(session, frames.Skip(400));
            Assert.That(session.Coverage.Fraction, Is.GreaterThanOrEqualTo(before));
            Assert.That(
                session.Passes.Select(p => p.Reason),
                Is.EqualTo(new[] { "start", "resume" })
            );
            Assert.That(
                session.ActiveSeconds,
                Is.EqualTo((frames.Count - 100 - 2) / 30f).Within(0.1f),
                "the pause is not active time"
            );

            Assert.That(session.Interrupt(), Is.True);
            Assert.That(session.StartOver(), Is.True);
            Assert.That(session.State, Is.EqualTo(CaptureState.Framing));
            Assert.That(session.Mode, Is.EqualTo(CaptureMode.Room), "Start over keeps the mode");
            Assert.That(session.Frames.Count, Is.EqualTo(0));
            Assert.That(session.Coverage.Fraction, Is.EqualTo(0f));
            Assert.That(session.CanStartRecording, Is.False, "tracking is found again first");
        }

        [Test]
        public void ActionsInTheWrongStateAreRefusedNotThrown()
        {
            var session = new CaptureSession(CaptureMode.Tabletop, firstRun: false);
            Assert.DoesNotThrow(() =>
            {
                Assert.That(session.Finish(), Is.False);
                Assert.That(session.Resume(), Is.False);
                Assert.That(session.Interrupt(), Is.False);
                Assert.That(session.KeepRecording(), Is.False);
                Assert.That(session.UploadAnyway(), Is.False);
                Assert.That(session.Confirm(), Is.False);
                Assert.That(session.Retake(), Is.False);
                session.AddFrame(
                    new CaptureFrame(
                        0,
                        0,
                        Vector3.zero,
                        Quaternion.identity,
                        TrackingQuality.Normal,
                        100f,
                        0.5f,
                        false
                    )
                );
            });
            Assert.That(session.Frames.Count, Is.EqualTo(0));
        }

        [Test]
        public void RetakeFromTheGateOrPreview_ClearsAndKeepsTheMode()
        {
            var session = Recording(CaptureMode.Tabletop);
            Feed(session, new SyntheticCapture().Generate(CaptureMode.Tabletop));
            Assert.That(session.Finish(), Is.True);
            Assert.That(
                session.State,
                Is.EqualTo(CaptureState.QualityGate),
                "nothing missed: straight to the gate"
            );
            Assert.That(session.UploadAnyway(), Is.True);
            Assert.That(session.Retake(), Is.True);
            Assert.That(session.State, Is.EqualTo(CaptureState.Framing));
            Assert.That(session.Mode, Is.EqualTo(CaptureMode.Tabletop));
        }

        [Test]
        public void FirstRunCoachThroughShowsOnce()
        {
            var session = Recording(CaptureMode.Room, firstRun: true);
            Assert.That(session.DrainCues(), Has.Member(CaptureCueKind.FirstRunCoachThrough));
            Feed(session, new SyntheticCapture { Seconds = 5f }.Generate(CaptureMode.Room));
            session.Interrupt();
            session.StartOver();
            session.ReportFramingTracking(TrackingQuality.Normal);
            session.StartRecording();
            Assert.That(session.DrainCues(), Has.No.Member(CaptureCueKind.FirstRunCoachThrough));

            var later = Recording(CaptureMode.Room, firstRun: false);
            Assert.That(later.DrainCues(), Has.No.Member(CaptureCueKind.FirstRunCoachThrough));
        }

        [Test]
        public void ReconstructionFailure_GivesAFreeRetryInTheSameMode()
        {
            var retry = CaptureSession.RetryAfterReconstructionFailure(CaptureMode.Tabletop);
            Assert.That(retry.Mode, Is.EqualTo(CaptureMode.Tabletop));
            Assert.That(retry.State, Is.EqualTo(CaptureState.Framing));
            Assert.That(retry.RetryMessage, Is.EqualTo(CoachingCopy.ReconstructionFailed));
        }

        [Test]
        public void LongCapture_TurnsTheRingAmberAndCoachesDuration()
        {
            var session = Recording(CaptureMode.Room);
            var cues = Feed(
                session,
                new SyntheticCapture { Seconds = 200f }.Generate(CaptureMode.Room)
            );
            Assert.That(cues, Has.Member(CaptureCueKind.LongCapture));
            Assert.That(session.RingAmber, Is.True);
            Assert.That(session.RingProgress, Is.EqualTo(1f));
            Assert.That(session.Readiness.Weakest, Is.EqualTo(ReadinessWeakness.Duration));
            Assert.That(session.GateMessage, Is.EqualTo(CoachingCopy.LongCapture));
        }

        [Test]
        public void ReadinessWeightsSumToOne()
        {
            float sum =
                CaptureTuning.Readiness.WeightCoverage
                + CaptureTuning.Readiness.WeightParallax
                + CaptureTuning.Readiness.WeightSharpness
                + CaptureTuning.Readiness.WeightLight
                + CaptureTuning.Readiness.WeightTracking;
            Assert.That(sum, Is.EqualTo(1f).Within(1e-5f));
            Assert.That(
                new ReadinessScore(1f, 1f, 1f, 1f, 1f, 60f).Score,
                Is.EqualTo(1f).Within(1e-5f)
            );
            Assert.That(new ReadinessScore(0f, 0f, 0f, 0f, 0f, 60f).Score, Is.EqualTo(0f));
        }

        [Test]
        public void PassesNeverExceedTheBundleLimit()
        {
            var session = Recording(CaptureMode.Room);
            var frames = new SyntheticCapture().Generate(CaptureMode.Room);
            int next = 0;
            for (int k = 0; k < 10; k++)
            {
                Feed(session, frames.Skip(next).Take(60));
                next += 60;
                session.Interrupt();
                session.Resume();
            }

            Assert.That(session.Passes.Count, Is.EqualTo(CapturePass.MaxPasses));
            Assert.That(session.Passes[session.Passes.Count - 1].LastFrame, Is.EqualTo(next - 1));
        }
    }
}
