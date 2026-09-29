using System;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Controls;

namespace GiganticJourneys.Movement.Intent
{
    /// <summary>
    /// Bluetooth/USB gamepad (left stick + south button) via the Input System, plus WASD/space
    /// for Editor testing. The gamepad stick keeps the Input System's default stick deadzone.
    /// </summary>
    public sealed class GamepadIntentSource : IIntentSource, IDisposable
    {
        readonly InputAction _move;
        readonly InputAction _jump;

        public GamepadIntentSource()
        {
            _move = new InputAction(
                "gj-move",
                InputActionType.Value,
                expectedControlType: "Vector2"
            );
            _move.AddBinding("<Gamepad>/leftStick");
            _move
                .AddCompositeBinding("2DVector")
                .With("Up", "<Keyboard>/w")
                .With("Down", "<Keyboard>/s")
                .With("Left", "<Keyboard>/a")
                .With("Right", "<Keyboard>/d");
            _jump = new InputAction("gj-jump", InputActionType.Button);
            _jump.AddBinding("<Gamepad>/buttonSouth");
            _jump.AddBinding("<Keyboard>/space");
            _move.Enable();
            _jump.Enable();
        }

        public IntentFrame Read() =>
            new IntentFrame(
                _move.ReadValue<Vector2>(),
                _jump.WasPressedThisFrame(),
                _jump.IsPressed()
            );

        public void Dispose()
        {
            _move.Dispose();
            _jump.Dispose();
        }
    }

    /// <summary>
    /// Touch: a floating stick anywhere in the left third of the safe area and a jump pad
    /// low-right (DESIGN_SYSTEM decision 5). Reads <see cref="Touchscreen.current"/> directly so
    /// it works without UI raycasts; the right half outside the pad is reserved for camera orbit (M1).
    /// </summary>
    public sealed class TouchIntentSource : IIntentSource
    {
        readonly FloatingStick _stick = new FloatingStick();

        /// <summary>Test hook: fixes the layout instead of reading Screen.safeArea / dpi.</summary>
        public TouchLayout? LayoutOverride;

        public FloatingStick Stick => _stick;

        public TouchLayout Layout =>
            LayoutOverride
            ?? new TouchLayout(Screen.safeArea, TouchLayout.PixelsPerPoint(Screen.dpi));

        public bool JumpHeld { get; private set; }

        public IntentFrame Read()
        {
            var screen = Touchscreen.current;
            if (screen == null)
            {
                _stick.End();
                JumpHeld = false;
                return IntentFrame.None;
            }
            var layout = Layout;
            var jumpPressed = false;
            var jumpHeld = false;
            var stickSeen = false;
            foreach (TouchControl touch in screen.touches)
            {
                var id = touch.touchId.ReadValue();
                var inProgress = touch.isInProgress;
                var start = touch.startPosition.ReadValue();
                if (_stick.Active && id == _stick.TouchId)
                {
                    if (inProgress)
                    {
                        stickSeen = true;
                        _stick.Drag(touch.position.ReadValue(), layout.StickRadius);
                    }
                    continue;
                }
                if (!inProgress)
                    continue;
                if (!_stick.Active && !stickSeen && layout.InStickZone(start))
                {
                    _stick.Begin(id, start);
                    _stick.Drag(touch.position.ReadValue(), layout.StickRadius);
                    stickSeen = true;
                    continue;
                }
                if (layout.OnJumpPad(start))
                {
                    jumpHeld = true;
                    if (touch.press.wasPressedThisFrame)
                        jumpPressed = true;
                }
            }
            if (_stick.Active && !stickSeen)
                _stick.End();
            JumpHeld = jumpHeld;
            return new IntentFrame(_stick.Value, jumpPressed, jumpHeld);
        }
    }
}
