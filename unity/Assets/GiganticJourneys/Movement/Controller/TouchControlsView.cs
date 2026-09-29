using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UIElements;

namespace GiganticJourneys.Movement.Controller
{
    /// <summary>
    /// Draws the touch controls of a <see cref="TraversalController"/> with UI Toolkit: the jump
    /// pad low-right and, while a thumb is down in the left third, the floating stick base and
    /// knob (DESIGN_SYSTEM decision 5). Purely visual: input is read by
    /// <see cref="GiganticJourneys.Movement.Intent.TouchIntentSource"/>. Placeholder styling until
    /// the design tokens land (M0-DSGN-02).
    /// </summary>
    public sealed class TouchControlsView : MonoBehaviour
    {
        [SerializeField]
        TraversalController controller;

        [Tooltip("Show the jump pad even without a touchscreen (Editor evidence captures).")]
        [SerializeField]
        bool showWithoutTouchscreen;

        PanelSettings _panel;
        UIDocument _document;
        VisualElement _jump;
        VisualElement _stickBase;
        VisualElement _stickKnob;

        public TraversalController Controller
        {
            get => controller;
            set => controller = value;
        }

        public bool ShowWithoutTouchscreen
        {
            get => showWithoutTouchscreen;
            set => showWithoutTouchscreen = value;
        }

        /// <summary>Evidence/test hook: the panel's pixel height when it renders to a texture instead of the screen.</summary>
        public float? ViewportHeightOverride { get; set; }

        public PanelSettings Panel => _panel;

        public VisualElement JumpPad => _jump;
        public VisualElement StickBase => _stickBase;
        public VisualElement StickKnob => _stickKnob;

        void Awake()
        {
            var filter = Debug.unityLogger.filterLogType;
            Debug.unityLogger.filterLogType = LogType.Error;
            try
            {
                _panel = ScriptableObject.CreateInstance<PanelSettings>();
            }
            finally
            {
                Debug.unityLogger.filterLogType = filter;
            }
            _panel.name = "GJ Touch Controls Panel";
            _panel.scaleMode = PanelScaleMode.ConstantPixelSize;
            _panel.scale = 1f;
            _panel.clearColor = false;
            _panel.themeStyleSheet = ScriptableObject.CreateInstance<ThemeStyleSheet>();
            _document = gameObject.AddComponent<UIDocument>();
            _document.panelSettings = _panel;
            var root = _document.rootVisualElement;
            root.pickingMode = PickingMode.Ignore;
            _jump = Circle("gj-jump-pad", true);
            _stickBase = Circle("gj-stick-base", false);
            _stickKnob = Circle("gj-stick-knob", true);
            root.Add(_jump);
            root.Add(_stickBase);
            root.Add(_stickKnob);
        }

        void OnDestroy()
        {
            if (_panel != null)
            {
                Destroy(_panel.themeStyleSheet);
                Destroy(_panel);
            }
        }

        static VisualElement Circle(string name, bool filled)
        {
            var e = new VisualElement { name = name, pickingMode = PickingMode.Ignore };
            e.style.position = Position.Absolute;
            var edge = new Color(1f, 1f, 1f, 0.85f);
            e.style.borderTopColor = edge;
            e.style.borderBottomColor = edge;
            e.style.borderLeftColor = edge;
            e.style.borderRightColor = edge;
            e.style.backgroundColor = filled
                ? new Color(1f, 1f, 1f, 0.55f)
                : new Color(0f, 0f, 0f, 0.12f);
            return e;
        }

        void Place(VisualElement e, Vector2 screenCenter, float radius)
        {
            var viewportHeight = ViewportHeightOverride ?? Screen.height;
            // Screen space is y-up; the panel is y-down at 1 px per unit (ConstantPixelSize, scale 1).
            var size = radius * 2f;
            e.style.left = screenCenter.x - radius;
            e.style.top = viewportHeight - screenCenter.y - radius;
            e.style.width = size;
            e.style.height = size;
            var r = new Length(radius, LengthUnit.Pixel);
            e.style.borderTopLeftRadius = r;
            e.style.borderTopRightRadius = r;
            e.style.borderBottomLeftRadius = r;
            e.style.borderBottomRightRadius = r;
            var w = Mathf.Max(1f, radius * 0.06f);
            e.style.borderTopWidth = w;
            e.style.borderBottomWidth = w;
            e.style.borderLeftWidth = w;
            e.style.borderRightWidth = w;
        }

        void LateUpdate()
        {
            if (controller == null || _jump == null)
                return;
            var visible = Touchscreen.current != null || showWithoutTouchscreen;
            var touch = controller.Touch;
            var layout = touch.Layout;
            _jump.style.display = visible ? DisplayStyle.Flex : DisplayStyle.None;
            if (visible)
            {
                Place(_jump, layout.JumpCenter, layout.JumpRadius);
                _jump.style.opacity = touch.JumpHeld ? 1f : 0.6f;
                _jump.style.backgroundColor = touch.JumpHeld
                    ? new Color(1f, 1f, 1f, 0.8f)
                    : new Color(1f, 1f, 1f, 0.3f);
            }
            var stick = touch.Stick;
            var showStick = visible && stick.Active;
            _stickBase.style.display = showStick ? DisplayStyle.Flex : DisplayStyle.None;
            _stickKnob.style.display = showStick ? DisplayStyle.Flex : DisplayStyle.None;
            if (showStick)
            {
                Place(_stickBase, stick.Origin, layout.StickRadius);
                Place(
                    _stickKnob,
                    stick.Origin + stick.Value * layout.StickRadius,
                    layout.StickRadius * 0.45f
                );
            }
        }
    }
}
