using System;
using System.Collections.Generic;
using System.IO;
using GiganticJourneys.Movement;
using UnityEngine;

namespace GiganticJourneys.Avatars
{
    /// <summary>
    /// The preset character roster (M1-AVAT-01): <c>roster.json</c> plus one avatar_params per
    /// preset, shipped byte-identical from <c>data/avatar/roster/</c> to
    /// <c>StreamingAssets/avatar/roster/</c> (<c>.github/scripts/copy_roster_to_unity.py</c>).
    /// Label, gender presentation and apparent age are casting metadata and are never shown
    /// to the player. Player-facing copy says "your character" (DESIGN_SYSTEM §9).
    /// </summary>
    public sealed class CharacterRoster
    {
        public const string RelativeDirectory = "avatar/roster";
        public const string ManifestName = "roster.json";

        public sealed class Preset
        {
            public string PresetId;
            public Color HeroColor;
            public AvatarParams Params;
        }

        public string RosterVersion { get; private set; }
        public int Floor { get; private set; }
        public readonly List<Preset> Presets = new List<Preset>();

        public static string DefaultDirectory =>
            Path.Combine(Application.streamingAssetsPath, RelativeDirectory);

        public Preset Find(string presetId) => Presets.Find(p => p.PresetId == presetId);

        /// <summary>Loads and checks the roster in <paramref name="directory"/> (default: StreamingAssets).</summary>
        public static CharacterRoster Load(string directory = null)
        {
            directory ??= DefaultDirectory;
            var manifestPath = Path.Combine(directory, ManifestName);
            if (!File.Exists(manifestPath))
                throw new AvatarParamsException($"{ManifestName} missing in {directory}");
            Dictionary<string, object> m;
            try
            {
                m = StrictJson.Parse(File.ReadAllText(manifestPath)) as Dictionary<string, object>;
            }
            catch (FormatException e)
            {
                throw new AvatarParamsException($"{ManifestName}: {e.Message}");
            }
            if (m == null)
                throw new AvatarParamsException($"{ManifestName} must be an object");
            if (!(m.TryGetValue("base_rig", out var rig) && rig as string == AvatarParams.BaseRig))
                throw new AvatarParamsException(
                    $"{ManifestName}: base_rig must be {AvatarParams.BaseRig}"
                );
            var roster = new CharacterRoster
            {
                RosterVersion = m.TryGetValue("roster_version", out var v) ? v as string : null,
                Floor = m.TryGetValue("floor", out var f) && f is double fd ? (int)fd : 6,
            };
            if (!(m.TryGetValue("presets", out var list) && list is List<object> entries))
                throw new AvatarParamsException($"{ManifestName}: presets must be an array");
            foreach (var e in entries)
            {
                if (!(e is Dictionary<string, object> entry))
                    throw new AvatarParamsException($"{ManifestName}: presets[] must be objects");
                var id = entry.TryGetValue("preset_id", out var idv) ? idv as string : null;
                var file = entry.TryGetValue("file", out var fv) ? fv as string : null;
                var hex = entry.TryGetValue("hero_color", out var hv) ? hv as string : null;
                if (id == null || file == null || hex == null)
                    throw new AvatarParamsException(
                        $"{ManifestName}: preset entries need preset_id, file, hero_color"
                    );
                if (file.Contains("..") || Path.IsPathRooted(file) || file.Contains(":"))
                    throw new AvatarParamsException(
                        $"{id}: file must stay inside the roster directory"
                    );
                if (roster.Find(id) != null)
                    throw new AvatarParamsException($"duplicate preset_id {id}");
                if (!ColorUtility.TryParseHtmlString(hex, out var hero))
                    throw new AvatarParamsException($"{id}: hero_color '{hex}' is not a colour");
                var path = Path.Combine(directory, file);
                if (!File.Exists(path))
                    throw new AvatarParamsException($"{id}: {file} missing");
                AvatarParams p;
                try
                {
                    p = AvatarParams.Parse(File.ReadAllText(path));
                }
                catch (AvatarParamsException ex)
                {
                    throw new AvatarParamsException($"{id}: {ex.Message}");
                }
                if (p.Source != "preset" || p.PresetId != id)
                    throw new AvatarParamsException($"{id}: provenance must be preset '{id}'");
                roster.Presets.Add(
                    new Preset
                    {
                        PresetId = id,
                        HeroColor = hero,
                        Params = p,
                    }
                );
            }
            if (roster.Presets.Count < roster.Floor)
                throw new AvatarParamsException(
                    $"roster has {roster.Presets.Count} presets, below the floor of {roster.Floor}"
                );
            return roster;
        }
    }
}
