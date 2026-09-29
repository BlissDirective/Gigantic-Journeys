using System;
using System.Collections;
using System.IO;
using GiganticJourneys.Movement.Controller;
using GiganticJourneys.Movement.Intent;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// Evidence capture for M0-UNITY-03 AT-5 (not a CI test): renders the movement test scene with
    /// simulated touch input into a 1920×1080 texture, with the touch controls composited, and
    /// writes PNGs to <c>$GJ_EVIDENCE_OUT</c>. Needs a graphics device: run with
    /// <c>-testFilter MovementEvidenceCapture</c> under xvfb with <c>-force-vulkan -force-device-index 0</c>
    /// (no <c>-nographics</c>).
    /// </summary>
    [Explicit("evidence capture; needs a graphics device")]
    [Category("Evidence")]
    public class MovementEvidenceCapture
    {
        const int Width = 1920;
        const int Height = 1080;

        [UnityTest]
        public IEnumerator Capture_TouchControlsInTheMovementTestScene()
        {
            var outDir = Environment.GetEnvironmentVariable("GJ_EVIDENCE_OUT");
            if (string.IsNullOrEmpty(outDir))
                outDir = Path.Combine(Application.temporaryCachePath, "gj-movement-evidence");
            Directory.CreateDirectory(outDir);
            InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
            InputSystem.settings.editorInputBehaviorInPlayMode = InputSettings
                .EditorInputBehaviorInPlayMode
                .AllDeviceInputAlwaysGoesToGameView;

            yield return SceneManager.LoadSceneAsync("MovementTest", LoadSceneMode.Single);
            var controller = UnityEngine.Object.FindAnyObjectByType<TraversalController>();
            var view = UnityEngine.Object.FindAnyObjectByType<TouchControlsView>();
            var cam = Camera.main;
            Assert.That(controller != null && view != null && cam != null);

            var layout = new TouchLayout(new Rect(0, 0, Width, Height), 2f); // an @2x phone
            controller.Touch.LayoutOverride = layout;
            view.ShowWithoutTouchscreen = true;
            view.ViewportHeightOverride = Height;
            var rt = new RenderTexture(Width, Height, 24);
            cam.targetTexture = rt;
            view.Panel.targetTexture = rt;

            var screen = InputSystem.AddDevice<Touchscreen>();
            try
            {
                var origin = new Vector2(330f, 280f);
                Touch(screen, 1, UnityEngine.InputSystem.TouchPhase.Began, origin, origin);
                yield return null;
                var drag = origin + new Vector2(0.35f, 0.94f) * layout.StickRadius;
                Touch(screen, 1, UnityEngine.InputSystem.TouchPhase.Moved, drag, origin);
                yield return new WaitForSeconds(1.2f);
                yield return Save(rt, Path.Combine(outDir, "01-touch-stick-run.png"));
                Debug.Log(
                    $"[GJ-EVIDENCE] 01 gait={controller.Motor.Gait} verb={controller.Motor.Verb} "
                        + $"stick={controller.LastIntent.Move} pos={controller.transform.position}"
                );

                Touch(
                    screen,
                    2,
                    UnityEngine.InputSystem.TouchPhase.Began,
                    layout.JumpCenter,
                    layout.JumpCenter
                );
                yield return new WaitForSeconds(0.45f);
                yield return Save(rt, Path.Combine(outDir, "02-touch-jump-pad-running-jump.png"));
                Debug.Log(
                    $"[GJ-EVIDENCE] 02 verb={controller.Motor.Verb} lastJump={controller.Motor.LastJumpVerb} "
                        + $"grounded={controller.Motor.Grounded}"
                );
            }
            finally
            {
                InputSystem.RemoveDevice(screen);
                cam.targetTexture = null;
                if (view != null && view.Panel != null)
                    view.Panel.targetTexture = null;
                rt.Release();
            }
        }

        static void Touch(
            Touchscreen s,
            int id,
            UnityEngine.InputSystem.TouchPhase phase,
            Vector2 pos,
            Vector2 start
        ) =>
            InputSystem.QueueStateEvent(
                s,
                new TouchState
                {
                    touchId = id,
                    phase = phase,
                    position = pos,
                    startPosition = start,
                }
            );

        static IEnumerator Save(RenderTexture rt, string path)
        {
            yield return null;
            yield return null;
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(Width, Height, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, Width, Height), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            File.WriteAllBytes(path, tex.EncodeToPNG());
            UnityEngine.Object.Destroy(tex);
            Debug.Log($"[GJ-EVIDENCE] wrote {path}");
        }
    }
}
