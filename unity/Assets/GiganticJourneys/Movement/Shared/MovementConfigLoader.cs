using System;
using System.IO;
using UnityEngine;

namespace GiganticJourneys.Movement
{
    /// <summary>
    /// Loads <c>StreamingAssets/movement.json</c> (the byte-identical copy of
    /// <c>config/movement.json</c> kept in sync by CI movement-sync) once at startup, before the
    /// first scene loads (ticket M0-UNITY-03 AT-2). A missing, malformed or off-contract file is
    /// a hard error: it is logged with the offending key and <see cref="Current"/> rethrows it.
    /// </summary>
    public static class MovementConfigLoader
    {
        public const string FileName = "movement.json";

        static MovementConfig _current;
        static MovementConfigException _loadError;

        /// <summary>Full path of the shipped movement.json.</summary>
        public static string DefaultPath => Path.Combine(Application.streamingAssetsPath, FileName);

        /// <summary>The startup config. Throws the load error if movement.json was rejected.</summary>
        public static MovementConfig Current
        {
            get
            {
                if (_current == null && _loadError == null)
                    LoadAtStartup();
                if (_loadError != null)
                    throw _loadError;
                return _current;
            }
        }

        /// <summary>Reads and strictly parses a movement.json file.</summary>
        public static MovementConfig LoadFile(string path)
        {
            string text;
            try
            {
                // iOS (the v1 platform) and the Editor expose StreamingAssets as plain files.
                text = File.ReadAllText(path);
            }
            catch (Exception e)
            {
                throw new MovementConfigException($"cannot read {path}: {e.Message}", e);
            }
            return MovementConfig.Parse(text, path);
        }

        /// <summary>Replaces the process-wide config (tests, and M1 live tuning).</summary>
        public static void Override(MovementConfig config)
        {
            _current = config ?? throw new ArgumentNullException(nameof(config));
            _loadError = null;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void LoadAtStartup()
        {
            try
            {
                _current = LoadFile(DefaultPath);
                _loadError = null;
            }
            catch (MovementConfigException e)
            {
                _current = null;
                _loadError = e;
                Debug.LogError($"[GJ-MOVEMENT] {e.Message}");
            }
        }
    }
}
