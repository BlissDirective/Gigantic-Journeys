using System.Collections;
using System.Collections.Generic;
using GiganticJourneys.Movement;
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
    /// The capsule controller with real CharacterController physics on a flat floor
    /// (M0-UNITY-03 AT-3 speeds, AT-4 jumps, AT-5 touch + gamepad → one intent layer).
    /// </summary>
    public class TraversalControllerPlayModeTests
    {
        sealed class Scripted : IIntentSource
        {
            public Vector2 Move;
            public bool JumpNext;

            public IntentFrame Read()
            {
                var f = new IntentFrame(Move, JumpNext, JumpNext);
                JumpNext = false;
                return f;
            }
        }

        readonly List<Object> _spawned = new List<Object>();
        readonly List<InputDevice> _devices = new List<InputDevice>();
        int _targetFrameRate;
        InputSettings.EditorInputBehaviorInPlayMode _editorBehavior;
        InputSettings.BackgroundBehavior _background;

        [SetUp]
        public void SetUp()
        {
            _targetFrameRate = Application.targetFrameRate;
            Application.targetFrameRate = 60;
            _editorBehavior = InputSystem.settings.editorInputBehaviorInPlayMode;
            _background = InputSystem.settings.backgroundBehavior;
            InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
            InputSystem.settings.editorInputBehaviorInPlayMode = InputSettings
                .EditorInputBehaviorInPlayMode
                .AllDeviceInputAlwaysGoesToGameView;
            var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
            floor.name = "test-floor";
            floor.transform.localScale = new Vector3(4f, 1f, 4f); // 40 m square
            _spawned.Add(floor);
        }

        [TearDown]
        public void TearDown()
        {
            foreach (var o in _spawned)
            {
                if (o != null)
                    Object.Destroy(o);
            }
            _spawned.Clear();
            foreach (var d in _devices)
                InputSystem.RemoveDevice(d);
            _devices.Clear();
            Application.targetFrameRate = _targetFrameRate;
            InputSystem.settings.editorInputBehaviorInPlayMode = _editorBehavior;
            InputSystem.settings.backgroundBehavior = _background;
        }

        TraversalController Spawn(Vector3 at, IIntentSource script = null)
        {
            var go = new GameObject("test-capsule");
            go.transform.position = at;
            var c = go.AddComponent<TraversalController>();
            c.IntentOverride = script;
            _spawned.Add(go);
            return c;
        }

        static IEnumerator Settle(TraversalController c)
        {
            for (var i = 0; i < 30 && !c.Motor.Grounded; i++)
                yield return null;
            Assert.That(c.Motor.Grounded, Is.True, "capsule settles on the floor");
        }

        [UnityTest]
        public IEnumerator Capsule_IsSizedInA_FromMovementJson()
        {
            var c = Spawn(Vector3.zero, new Scripted());
            yield return null;
            var s = c.Scale;
            Assert.That(c.Body.height, Is.EqualTo(s.ToWorld(c.Config.AvatarHeightA)).Within(1e-5f));
            Assert.That(
                c.Body.stepOffset,
                Is.EqualTo(s.ToWorld(c.Config.Verticals.StepUp)).Within(1e-5f)
            );
            Assert.That(c.Body.slopeLimit, Is.EqualTo(c.Config.Slopes.RunMaxDeg));
            Assert.That(s.WorldUnitsPerA, Is.EqualTo(1.75f / 12f).Within(1e-4f), "1:12 default");
        }

        [UnityTest]
        public IEnumerator WalkJogRunSprint_Over5Seconds_WithinTwoPercent()
        {
            var sticks = new[] { 0.3f, 0.6f, 1f, 1f };
            var gaits = new[] { Gait.Walk, Gait.Jog, Gait.Run, Gait.Sprint };
            var caps = new TraversalController[4];
            for (var i = 0; i < 4; i++)
                caps[i] = Spawn(new Vector3(i * 2f - 3f, 0.01f, -15f), new Scripted());
            foreach (var c in caps)
                yield return Settle(c);
            for (var i = 0; i < 4; i++)
                ((Scripted)caps[i].IntentOverride).Move = new Vector2(0f, sticks[i]);
            // Run held 1.5 s becomes sprint (Bible §3.1): cap the run capsule to time a full 5 s run.
            caps[2].Motor.MaxGait = Gait.Run;
            // Let sprint engage (run held 1.5 s) before measuring.
            yield return new WaitForSeconds(ProvisionalTuning.Intent.SprintHoldSec + 0.2f);
            var z0 = new float[4];
            for (var i = 0; i < 4; i++)
                z0[i] = caps[i].transform.position.z;
            var t0 = Time.time;
            while (Time.time - t0 < 5f)
                yield return null;
            var elapsed = Time.time - t0;
            for (var i = 0; i < 4; i++)
            {
                var c = caps[i];
                Assert.That(c.Motor.Gait, Is.EqualTo(gaits[i]));
                var speedA = c.Scale.ToA(c.transform.position.z - z0[i]) / elapsed;
                var expected = GaitSelector.SpeedA(gaits[i], c.Config);
                Debug.Log(
                    $"[M0-UNITY-03 AT-3] {gaits[i]}: {speedA:0.000} A/s over {elapsed:0.00} s (target {expected})"
                );
                Assert.That(
                    speedA,
                    Is.EqualTo(expected).Within(expected * 0.02f),
                    gaits[i].ToString()
                );
            }
        }

        IEnumerator MeasureJump(
            TraversalController c,
            Scripted s,
            Vector2 stick,
            List<float> result
        )
        {
            var start = c.transform.position;
            var peak = start.y;
            s.Move = stick;
            s.JumpNext = true;
            yield return null;
            Assert.That(c.Motor.Grounded, Is.False, "took off");
            var frames = 0;
            while (!c.Motor.Grounded && frames++ < 600)
            {
                peak = Mathf.Max(peak, c.transform.position.y);
                yield return null;
            }
            var land = c.transform.position;
            var d = land - start;
            d.y = 0f;
            result.Add(c.Scale.ToA(peak - start.y));
            result.Add(c.Scale.ToA(d.magnitude));
        }

        [UnityTest]
        public IEnumerator StandingAndRunningJump_HeightAndDistance_WithinFivePercent()
        {
            var s = new Scripted();
            var c = Spawn(new Vector3(0f, 0.01f, -15f), s);
            yield return Settle(c);
            var standing = new List<float>();
            yield return MeasureJump(c, s, new Vector2(0f, 0.3f), standing);
            Assert.That(c.Motor.LastJumpVerb, Is.EqualTo(Verbs.StandingJump));
            var j = c.Config.Jump;
            Debug.Log(
                $"[M0-UNITY-03 AT-4] standing jump: height {standing[0]:0.000} A, distance {standing[1]:0.000} A"
            );
            Assert.That(standing[0], Is.EqualTo(j.StandingHeight).Within(j.StandingHeight * 0.05f));
            Assert.That(
                standing[1],
                Is.EqualTo(j.StandingDistance).Within(j.StandingDistance * 0.05f)
            );

            s.Move = Vector2.up;
            for (var i = 0; i < 20; i++)
                yield return null;
            var running = new List<float>();
            yield return MeasureJump(c, s, Vector2.up, running);
            Assert.That(c.Motor.LastJumpVerb, Is.EqualTo(Verbs.RunningJump));
            Debug.Log(
                $"[M0-UNITY-03 AT-4] running jump: height {running[0]:0.000} A, distance {running[1]:0.000} A"
            );
            Assert.That(running[0], Is.EqualTo(j.RunningHeight).Within(j.RunningHeight * 0.05f));
            Assert.That(
                running[1],
                Is.EqualTo(j.RunningDistance).Within(j.RunningDistance * 0.05f)
            );
        }

        [UnityTest]
        public IEnumerator Gamepad_DrivesTheIntentLayer()
        {
            var c = Spawn(new Vector3(0f, 0.01f, -15f));
            yield return Settle(c);
            var pad = InputSystem.AddDevice<Gamepad>();
            _devices.Add(pad);
            InputSystem.QueueStateEvent(pad, new GamepadState { leftStick = new Vector2(0f, 1f) });
            yield return null;
            var z0 = c.transform.position.z;
            for (var i = 0; i < 20; i++)
                yield return null;
            Assert.That(
                c.LastIntent.Move.y,
                Is.GreaterThan(0.85f),
                "stick read through the Input System"
            );
            Assert.That(c.Motor.Gait, Is.EqualTo(Gait.Run));
            Assert.That(c.transform.position.z, Is.GreaterThan(z0), "moved forward");

            InputSystem.QueueStateEvent(
                pad,
                new GamepadState { leftStick = new Vector2(0f, 1f) }.WithButton(GamepadButton.South)
            );
            yield return null;
            yield return null;
            Assert.That(c.Motor.Grounded, Is.False, "south button jumps");
            Assert.That(c.Motor.LastJumpVerb, Is.EqualTo(Verbs.RunningJump));
        }

        [UnityTest]
        public IEnumerator Touch_FloatingStickAndJumpPad_DriveTheSameIntentLayer()
        {
            var c = Spawn(new Vector3(0f, 0.01f, -15f));
            var layout = new TouchLayout(new Rect(0f, 0f, 1920f, 1080f), 1f);
            c.Touch.LayoutOverride = layout;
            yield return Settle(c);
            var screen = InputSystem.AddDevice<Touchscreen>();
            _devices.Add(screen);

            var origin = new Vector2(300f, 300f); // left third
            InputSystem.QueueStateEvent(
                screen,
                new TouchState
                {
                    touchId = 1,
                    phase = UnityEngine.InputSystem.TouchPhase.Began,
                    position = origin,
                    startPosition = origin,
                }
            );
            yield return null;
            InputSystem.QueueStateEvent(
                screen,
                new TouchState
                {
                    touchId = 1,
                    phase = UnityEngine.InputSystem.TouchPhase.Moved,
                    position = origin + new Vector2(0f, layout.StickRadius),
                    startPosition = origin,
                }
            );
            yield return null;
            var z0 = c.transform.position.z;
            for (var i = 0; i < 20; i++)
                yield return null;
            Assert.That(
                c.Touch.Stick.Active,
                Is.True,
                "stick floats to the first touch in the left third"
            );
            Assert.That(c.Touch.Stick.Origin, Is.EqualTo(origin));
            Assert.That(c.LastIntent.Move.y, Is.EqualTo(1f).Within(1e-3f));
            Assert.That(c.Motor.Gait, Is.EqualTo(Gait.Run));
            Assert.That(c.transform.position.z, Is.GreaterThan(z0), "moved forward");

            InputSystem.QueueStateEvent(
                screen,
                new TouchState
                {
                    touchId = 2,
                    phase = UnityEngine.InputSystem.TouchPhase.Began,
                    position = layout.JumpCenter,
                    startPosition = layout.JumpCenter,
                }
            );
            yield return null;
            yield return null;
            Assert.That(c.Motor.Grounded, Is.False, "jump pad jumps");
            Assert.That(c.Motor.LastJumpVerb, Is.EqualTo(Verbs.RunningJump));

            InputSystem.QueueStateEvent(
                screen,
                new TouchState
                {
                    touchId = 1,
                    phase = UnityEngine.InputSystem.TouchPhase.Ended,
                    position = origin,
                    startPosition = origin,
                }
            );
            yield return null;
            yield return null;
            Assert.That(c.Touch.Stick.Active, Is.False, "stick releases");
        }

        [UnityTest]
        public IEnumerator MovementTestScene_LoadsWithControllerCameraAndTouchControls()
        {
            yield return SceneManager.LoadSceneAsync("MovementTest", LoadSceneMode.Additive);
            var scene = SceneManager.GetSceneByName("MovementTest");
            Assert.That(scene.isLoaded, Is.True);
            var controller = Object.FindAnyObjectByType<TraversalController>();
            Assert.That(controller, Is.Not.Null);
            Assert.That(controller.Motor, Is.Not.Null, "movement.json loaded");
            Assert.That(Object.FindAnyObjectByType<FollowCamera>(), Is.Not.Null);
            Assert.That(Object.FindAnyObjectByType<TouchControlsView>(), Is.Not.Null);
            for (var i = 0; i < 10; i++)
                yield return null;
            Assert.That(controller.Motor.Grounded, Is.True);
            yield return SceneManager.UnloadSceneAsync(scene);
        }
    }
}
