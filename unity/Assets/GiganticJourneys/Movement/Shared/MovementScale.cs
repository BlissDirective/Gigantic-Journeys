using System;

namespace GiganticJourneys.Movement
{
    /// <summary>
    /// Converts between A (one avatar height, Movement Bible §1) and world units, and derives
    /// gravity. All movement constants are in A so they survive the per-environment scale
    /// multiplier; the world is metric (a reconstructed room is in meters).
    /// <para>Bible §1: g = 9.81 × (1/scale) × gravityScale in world m/s², where scale is the
    /// environment multiplier (12 for 1:12). In A units that is 9.81 × gravityScale ÷ the
    /// avatar's real height in meters, independent of the environment multiplier.</para>
    /// </summary>
    public readonly struct MovementScale
    {
        /// <summary>Standard gravity in m/s², as written in Movement Bible §1.</summary>
        public const float StandardGravity = 9.81f;

        /// <summary>World units (meters) per A.</summary>
        public readonly float WorldUnitsPerA;

        /// <summary>Gravity in A/s².</summary>
        public readonly float GravityA;

        MovementScale(float worldUnitsPerA, float gravityA)
        {
            WorldUnitsPerA = worldUnitsPerA;
            GravityA = gravityA;
        }

        /// <param name="config">movement.json (avatarHeightA, gravityScale).</param>
        /// <param name="avatarRealHeightMeters">The character's real-world height (roster data; Bible §1 default).</param>
        /// <param name="environmentScale">The environment multiplier (12 = 1:12; from the environment spec in M1).</param>
        public static MovementScale Create(
            MovementConfig config,
            float avatarRealHeightMeters,
            float environmentScale
        )
        {
            if (config == null)
                throw new ArgumentNullException(nameof(config));
            if (avatarRealHeightMeters <= 0f)
                throw new ArgumentOutOfRangeException(nameof(avatarRealHeightMeters));
            if (environmentScale <= 0f)
                throw new ArgumentOutOfRangeException(nameof(environmentScale));
            var metersPerA = avatarRealHeightMeters * config.AvatarHeightA;
            return new MovementScale(
                metersPerA / environmentScale,
                StandardGravity * config.GravityScale / metersPerA
            );
        }

        public float ToWorld(float a) => a * WorldUnitsPerA;

        public float ToA(float world) => world / WorldUnitsPerA;
    }
}
