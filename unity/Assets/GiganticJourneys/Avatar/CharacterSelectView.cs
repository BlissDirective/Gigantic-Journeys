using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

namespace GiganticJourneys.Avatars
{
    /// <summary>
    /// The preset character picker (M1-AVAT-01). Shows one card per roster preset with its hero
    /// colour, applies the choice live to the rig, and remembers it. Copy says "your character"
    /// (DESIGN_SYSTEM §9, AUTH #044 addendum). Selection is shown by a check mark and a thick
    /// outline, never by hue alone (§10). Cards are at least 48 px. Preset path only: the custom,
    /// on-device create flow (M1-AVAT-02) is not built here.
    /// </summary>
    public sealed class CharacterSelectView : MonoBehaviour
    {
        public const string PrefsKey = "gj.character.preset";
        public const string Title = "Choose your character";
        public const string ConfirmLabel = "Play as this character";

        [Tooltip("The rig the choice is previewed on (optional).")]
        public AvatarAppearance preview;

        public CharacterRoster Roster { get; private set; }
        public string SelectedPresetId { get; private set; }
        public VisualElement Root { get; private set; }
        public IReadOnlyList<Button> Cards => _cards;

        /// <summary>Raised with the preset when the player confirms.</summary>
        public event Action<CharacterRoster.Preset> Confirmed;

        readonly List<Button> _cards = new List<Button>();
        PanelSettings _panel;
        UIDocument _document;

        /// <summary>The remembered preset, else the first preset in the roster.</summary>
        public static string RememberedOrDefault(CharacterRoster roster)
        {
            var id = PlayerPrefs.GetString(PrefsKey, null);
            return roster.Find(id) != null ? id : roster.Presets[0].PresetId;
        }

        /// <summary>Builds the picker for <paramref name="roster"/> (StreamingAssets when null).</summary>
        public void Show(CharacterRoster roster = null)
        {
            Roster = roster ?? CharacterRoster.Load();
            EnsurePanel();
            Root.Clear();
            _cards.Clear();

            var title = new Label(Title) { name = "gj-character-title" };
            title.style.fontSize = 28;
            title.style.unityFontStyleAndWeight = FontStyle.Bold;
            title.style.color = new Color(0.961f, 0.937f, 0.902f); // paper.cream
            title.style.marginBottom = 16;
            Root.Add(title);

            var grid = new VisualElement { name = "gj-character-grid" };
            grid.style.flexDirection = FlexDirection.Row;
            grid.style.flexWrap = Wrap.Wrap;
            grid.style.justifyContent = Justify.Center;
            Root.Add(grid);
            for (var i = 0; i < Roster.Presets.Count; i++)
            {
                var preset = Roster.Presets[i];
                var card = new Button(() => Select(preset.PresetId))
                {
                    name = "gj-character-" + preset.PresetId,
                    text = string.Empty,
                };
                card.tooltip = $"Character {i + 1}";
                card.style.width = 96;
                card.style.height = 120;
                card.style.marginLeft = card.style.marginRight = 8;
                card.style.marginTop = card.style.marginBottom = 8;
                card.style.backgroundColor = new Color(0.165f, 0.18f, 0.216f); // surface.charcoal
                var swatch = new VisualElement
                {
                    name = "swatch",
                    pickingMode = PickingMode.Ignore,
                };
                swatch.style.height = 64;
                swatch.style.backgroundColor = preset.HeroColor;
                swatch.style.borderTopLeftRadius = swatch.style.borderTopRightRadius = 6;
                card.Add(swatch);
                var number = new Label((i + 1).ToString())
                {
                    name = "number",
                    pickingMode = PickingMode.Ignore,
                };
                number.style.color = new Color(0.961f, 0.937f, 0.902f);
                number.style.unityTextAlign = TextAnchor.MiddleCenter;
                number.style.fontSize = 20;
                card.Add(number);
                var check = new Label("✓") { name = "check", pickingMode = PickingMode.Ignore };
                check.style.color = new Color(0.949f, 0.663f, 0.231f); // accent.amber on charcoal
                check.style.unityTextAlign = TextAnchor.MiddleCenter;
                check.style.fontSize = 20;
                card.Add(check);
                grid.Add(card);
                _cards.Add(card);
            }

            var confirm = new Button(Confirm)
            {
                name = "gj-character-confirm",
                text = ConfirmLabel,
            };
            confirm.style.minHeight = 48;
            confirm.style.marginTop = 16;
            confirm.style.fontSize = 20;
            Root.Add(confirm);

            Select(RememberedOrDefault(Roster));
        }

        public void Select(string presetId)
        {
            var preset = Roster?.Find(presetId);
            if (preset == null)
                return;
            SelectedPresetId = presetId;
            foreach (var card in _cards)
            {
                var on = card.name == "gj-character-" + presetId;
                var w = on ? 4f : 1f;
                var edge = on ? new Color(0.961f, 0.937f, 0.902f) : new Color(0.54f, 0.56f, 0.6f);
                card.style.borderTopWidth = card.style.borderBottomWidth = w;
                card.style.borderLeftWidth = card.style.borderRightWidth = w;
                card.style.borderTopColor = card.style.borderBottomColor = edge;
                card.style.borderLeftColor = card.style.borderRightColor = edge;
                card.Q<Label>("check").style.visibility = on
                    ? Visibility.Visible
                    : Visibility.Hidden;
            }
            if (preview != null)
                preview.Apply(preset.Params, preset.HeroColor);
        }

        public void Confirm()
        {
            var preset = Roster?.Find(SelectedPresetId);
            if (preset == null)
                return;
            PlayerPrefs.SetString(PrefsKey, preset.PresetId);
            PlayerPrefs.Save();
            Confirmed?.Invoke(preset);
        }

        void EnsurePanel()
        {
            if (Root != null)
                return;
            var filter = Debug.unityLogger.filterLogType;
            Debug.unityLogger.filterLogType = LogType.Error; // PanelSettings warns before a theme is set
            try
            {
                _panel = ScriptableObject.CreateInstance<PanelSettings>();
            }
            finally
            {
                Debug.unityLogger.filterLogType = filter;
            }
            _panel.name = "GJ Character Select Panel";
            _panel.scaleMode = PanelScaleMode.ScaleWithScreenSize;
            _panel.referenceResolution = new Vector2Int(1334, 750);
            _panel.themeStyleSheet = ScriptableObject.CreateInstance<ThemeStyleSheet>();
            _document = gameObject.AddComponent<UIDocument>();
            _document.panelSettings = _panel;
            Root = _document.rootVisualElement;
            Root.style.alignItems = Align.Center;
            Root.style.justifyContent = Justify.Center;
            Root.style.backgroundColor = new Color(0.11f, 0.122f, 0.149f, 0.92f); // ink.charcoal scrim
        }

        void OnDestroy()
        {
            if (_panel == null)
                return;
            DestroyObj(_panel.themeStyleSheet);
            DestroyObj(_panel);
        }

        static void DestroyObj(UnityEngine.Object o)
        {
            if (Application.isPlaying)
                Destroy(o);
            else
                DestroyImmediate(o);
        }
    }
}
