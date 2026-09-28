using System.Collections;
using System.IO;
using GiganticJourneys.DebugTools;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using UnityEngine.UIElements;

namespace GiganticJourneys.Tests
{
    /// <summary>The debug overlay at runtime (ticket M0-UNITY-04 AT-1, AT-3).</summary>
    public class DebugOverlayPlayModeTests
    {
        DebugOverlay _overlay;
        string _reportDir;
        InputSettings.EditorInputBehaviorInPlayMode _editorBehavior;
        InputSettings.BackgroundBehavior _background;

        [UnitySetUp]
        public IEnumerator SetUp()
        {
            yield return null;
            _overlay =
                DebugOverlay.Instance != null ? DebugOverlay.Instance : DebugOverlay.Create();
            _overlay.SetVisible(false);
            _reportDir = Path.Combine(Application.temporaryCachePath, "gj-overlay-tests");
            _overlay.ReportDirectory = _reportDir;
            // Batchmode has no focused Game view: route simulated input to the game anyway.
            _editorBehavior = InputSystem.settings.editorInputBehaviorInPlayMode;
            _background = InputSystem.settings.backgroundBehavior;
            InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
            InputSystem.settings.editorInputBehaviorInPlayMode = InputSettings
                .EditorInputBehaviorInPlayMode
                .AllDeviceInputAlwaysGoesToGameView;
        }

        [TearDown]
        public void TearDown()
        {
            InputSystem.settings.editorInputBehaviorInPlayMode = _editorBehavior;
            InputSystem.settings.backgroundBehavior = _background;
            DebugOverlay.SafeAreaOverride = null;
            DebugOverlay.PixelsPerPointOverride = null;
            if (_overlay != null)
            {
                _overlay.SetVisible(false);
                _overlay.ReportDirectory = null;
            }
            if (Directory.Exists(_reportDir))
                Directory.Delete(_reportDir, true);
        }

        [Test]
        public void Overlay_IsCreatedAutomatically_HiddenByDefault_WithUiToolkit()
        {
            Assert.That(DebugOverlay.Instance, Is.Not.Null);
            Assert.That(_overlay.Document, Is.Not.Null, "built with a UI Toolkit UIDocument");
            Assert.That(_overlay.Box.style.display.value, Is.EqualTo(DisplayStyle.None));
            Assert.That(_overlay.Visible, Is.False);
        }

        [UnityTest]
        public IEnumerator Visible_ShowsFpsP99FrameTimeBuildShaSceneDevice()
        {
            _overlay.SetVisible(true);
            yield return new WaitForSecondsRealtime(1.2f);
            _overlay.Refresh();
            var stats = _overlay.StatsLabel.text;
            var info = _overlay.InfoLabel.text;
            StringAssert.Contains("fps (1 s)", stats);
            StringAssert.Contains("p99", stats);
            StringAssert.Contains("(5 s)", stats);
            StringAssert.Contains(" ms", stats);
            StringAssert.Contains(Application.version, info);
            StringAssert.Contains(BuildInfo.GitSha, info);
            StringAssert.Contains(SceneManager.GetActiveScene().name, info);
            StringAssert.Contains(SystemInfo.deviceModel, info);
            Assert.That(_overlay.Stats.AverageFps(1f), Is.GreaterThan(0f));
        }

        [UnityTest]
        public IEnumerator Layout_TopRightInsideSafeArea_NoTallerThan8Percent()
        {
            // A notched-phone-like safe area: 7 % side insets, 5 % bottom inset.
            float w = Screen.width;
            float h = Screen.height;
            var safe = new Rect(w * 0.07f, h * 0.05f, w * 0.86f, h * 0.95f);
            DebugOverlay.SafeAreaOverride = safe;
            _overlay.SetVisible(true);
            yield return null;
            yield return null;
            yield return null;
            var r = _overlay.Box.worldBound;
            var landscapeH = Mathf.Min(w, h);
            Assert.That(r.height, Is.GreaterThan(0f), "overlay laid out");
            Assert.That(
                r.height,
                Is.LessThanOrEqualTo(landscapeH * DebugOverlay.LandscapeHeightFraction)
            );
            Assert.That(
                r.xMax,
                Is.LessThanOrEqualTo(safe.xMax + 0.5f),
                "inside the safe area (right)"
            );
            Assert.That(
                r.yMin,
                Is.GreaterThanOrEqualTo(h - safe.yMax - 0.5f),
                "inside the safe area (top)"
            );
            Assert.That(safe.xMax - r.xMax, Is.LessThan(landscapeH * 0.02f), "anchored right");
            Assert.That(r.yMin - (h - safe.yMax), Is.LessThan(landscapeH * 0.02f), "anchored top");
            Assert.That(
                _overlay.Box.resolvedStyle.backgroundColor.a,
                Is.GreaterThanOrEqualTo(0.6f),
                "scrim"
            );
        }

        [UnityTest]
        public IEnumerator SaveButton_BelowPanel_AtLeast44Points_InsideSafeArea(
            [Values(1f, 2f, 3f)] float pixelsPerPoint
        )
        {
            // Notched-phone-like safe area, as in the layout test, at 1x/2x/3x screen scale.
            float w = Screen.width;
            float h = Screen.height;
            var safe = new Rect(w * 0.07f, h * 0.05f, w * 0.86f, h * 0.95f);
            DebugOverlay.SafeAreaOverride = safe;
            DebugOverlay.PixelsPerPointOverride = pixelsPerPoint;
            _overlay.SetVisible(true);
            yield return null;
            yield return null;
            yield return null;
            var panel = _overlay.Box.worldBound;
            var button = _overlay.SaveButton.worldBound;
            var landscapeH = Mathf.Min(w, h);
            Assert.That(button.height, Is.GreaterThan(0f), "button laid out");
            Assert.That(
                panel.height,
                Is.LessThanOrEqualTo(landscapeH * DebugOverlay.LandscapeHeightFraction),
                "the panel alone stays inside the 8 % band"
            );
            Assert.That(
                _overlay.SaveButton.parent,
                Is.Not.SameAs(_overlay.Box),
                "button is not inside the panel"
            );
            Assert.That(
                button.yMin,
                Is.GreaterThanOrEqualTo(panel.yMax - 0.5f),
                "button sits below the panel"
            );
            Assert.That(
                button.height / pixelsPerPoint,
                Is.GreaterThanOrEqualTo(DebugOverlay.MinTouchTargetPoints - 0.01f),
                "button height >= 44 pt"
            );
            Assert.That(
                button.width / pixelsPerPoint,
                Is.GreaterThanOrEqualTo(DebugOverlay.MinTouchTargetPoints - 0.01f),
                "button width >= 44 pt"
            );
            Assert.That(
                button.xMax,
                Is.LessThanOrEqualTo(safe.xMax + 0.5f),
                "inside the safe area (right)"
            );
            Assert.That(
                button.yMax,
                Is.LessThanOrEqualTo(h - safe.yMin + 0.5f),
                "inside the safe area (bottom)"
            );
            Assert.That(
                Mathf.Abs(button.xMax - panel.xMax),
                Is.LessThan(1f),
                "right-aligned with the panel (top-right placement)"
            );
            Assert.That(
                button.yMin - panel.yMax,
                Is.LessThan(landscapeH * 0.02f),
                "directly below"
            );
        }

        [UnityTest]
        public IEnumerator F4_SavesReport_WhileVisible()
        {
            var keyboard = InputSystem.AddDevice<Keyboard>();
            keyboard.MakeCurrent();
            string saved = null;
            _overlay.ReportSaved += p => saved = p;
            try
            {
                InputSystem.QueueStateEvent(keyboard, new KeyboardState(Key.F4));
                yield return null;
                yield return null;
                Assert.That(saved, Is.Null, "F4 does nothing while the overlay is hidden");
                InputSystem.QueueStateEvent(keyboard, new KeyboardState());
                yield return null;
                _overlay.SetVisible(true);
                yield return null;
                InputSystem.QueueStateEvent(keyboard, new KeyboardState(Key.F4));
                yield return null;
                yield return null;
                Assert.That(saved, Is.Not.Null, "F4 saves a report while visible");
                Assert.That(File.Exists(saved), Is.True);
                InputSystem.QueueStateEvent(keyboard, new KeyboardState());
                yield return null;
            }
            finally
            {
                InputSystem.RemoveDevice(keyboard);
            }
        }

        [UnityTest]
        public IEnumerator F3_TogglesOverlay()
        {
            var keyboard = InputSystem.AddDevice<Keyboard>();
            keyboard.MakeCurrent();
            try
            {
                InputSystem.QueueStateEvent(keyboard, new KeyboardState(Key.F3));
                yield return null;
                yield return null;
                Assert.That(_overlay.Visible, Is.True, "F3 shows the overlay");
                InputSystem.QueueStateEvent(keyboard, new KeyboardState());
                yield return null;
                InputSystem.QueueStateEvent(keyboard, new KeyboardState(Key.F3));
                yield return null;
                yield return null;
                Assert.That(_overlay.Visible, Is.False, "F3 again hides it");
                InputSystem.QueueStateEvent(keyboard, new KeyboardState());
                yield return null;
            }
            finally
            {
                InputSystem.RemoveDevice(keyboard);
            }
        }

        [UnityTest]
        public IEnumerator ThreeFingerTap_TogglesOverlay()
        {
            var screen = InputSystem.AddDevice<Touchscreen>();
            screen.MakeCurrent();
            try
            {
                for (var i = 0; i < 3; i++)
                {
                    InputSystem.QueueStateEvent(
                        screen,
                        new TouchState
                        {
                            touchId = i + 1,
                            phase = UnityEngine.InputSystem.TouchPhase.Began,
                            position = new Vector2(100f + 60f * i, 100f),
                        }
                    );
                }
                yield return null;
                yield return null;
                Assert.That(_overlay.Visible, Is.True, "three fingers show the overlay");
                for (var i = 0; i < 3; i++)
                {
                    InputSystem.QueueStateEvent(
                        screen,
                        new TouchState
                        {
                            touchId = i + 1,
                            phase = UnityEngine.InputSystem.TouchPhase.Ended,
                            position = new Vector2(100f + 60f * i, 100f),
                        }
                    );
                }
                yield return null;
                yield return null;
                Assert.That(_overlay.Visible, Is.True, "lifting the fingers does not toggle");
            }
            finally
            {
                InputSystem.RemoveDevice(screen);
            }
        }

        [UnityTest]
        public IEnumerator SaveButton_WritesSixtySecondReport()
        {
            _overlay.SetVisible(true);
            yield return new WaitForSecondsRealtime(0.5f);
            string saved = null;
            _overlay.ReportSaved += p => saved = p;
            using (var e = NavigationSubmitEvent.GetPooled())
            {
                e.target = _overlay.SaveButton;
                _overlay.SaveButton.SendEvent(e);
            }
            yield return null;
            Assert.That(saved, Is.Not.Null, "the Save report button saved a report");
            Assert.That(File.Exists(saved), Is.True);
            StringAssert.StartsWith(_reportDir, saved);
            var text = File.ReadAllText(saved);
            StringAssert.Contains("fps_p50: ", text);
            StringAssert.Contains("fps_p99: ", text);
            StringAssert.Contains("window_s: 60.0", text);
            StringAssert.Contains("device_model: " + SystemInfo.deviceModel, text);
            StringAssert.Contains("build_version: " + Application.version, text);
            StringAssert.StartsWith(
                "Saved " + PerformanceReport.FilePrefix,
                _overlay.InfoLabel.text
            );
        }
    }
}
