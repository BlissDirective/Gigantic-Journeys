using System;
using System.Collections.Generic;
using System.Globalization;

namespace GiganticJourneys.Movement
{
    /// <summary>Raised when movement.json is unreadable, malformed, or has a missing or unknown key.</summary>
    public sealed class MovementConfigException : Exception
    {
        public MovementConfigException(string message)
            : base(message) { }

        public MovementConfigException(string message, Exception inner)
            : base(message, inner) { }
    }

    /// <summary>
    /// Typed view of <c>config/movement.json</c> (Movement Bible §10), the single source of truth
    /// for every movement constant, shared with the Python traversal validator
    /// (<c>services/traversal/movement.py</c>). Field names mirror the JSON keys 1:1. Parsing is
    /// strict: a missing or unknown key anywhere is a <see cref="MovementConfigException"/> naming
    /// the dotted path (ticket M0-UNITY-03 AT-2). Units: lengths in A (avatar heights), speeds in
    /// A/s, times in the unit named by the key (Ms, Sec), angles in degrees.
    /// </summary>
    public sealed class MovementConfig
    {
        public readonly float AvatarHeightA;
        public readonly SpeedsSection Speeds;
        public readonly JumpSection Jump;
        public readonly VerticalsSection Verticals;
        public readonly LandingSection Landing;
        public readonly SlopesSection Slopes;
        public readonly ReachSection Reach;
        public readonly float NarrowWidthA;
        public readonly float CrouchHeadroomA;
        public readonly float GravityScale;
        public readonly AssistSection Assist;
        public readonly DiveSection Dive;
        public readonly TicTacSection TicTac;
        public readonly WallRunSection WallRun;
        public readonly PoleVaultSection PoleVault;
        public readonly GrappleSection Grapple;

        /// <summary>Every constant by dotted JSON path, as read (floats as double, flags as bool).</summary>
        public readonly IReadOnlyDictionary<string, object> Values;

        MovementConfig(Reader r)
        {
            AvatarHeightA = r.Number("avatarHeightA");
            Speeds = new SpeedsSection(r.Object("speeds"));
            Jump = new JumpSection(r.Object("jump"));
            Verticals = new VerticalsSection(r.Object("verticals"));
            Landing = new LandingSection(r.Object("landing"));
            Slopes = new SlopesSection(r.Object("slopes"));
            Reach = new ReachSection(r.Object("reach"));
            NarrowWidthA = r.Number("narrowWidthA");
            CrouchHeadroomA = r.Number("crouchHeadroomA");
            GravityScale = r.Number("gravityScale");
            Assist = new AssistSection(r.Object("assist"));
            Dive = new DiveSection(r.Object("dive"));
            TicTac = new TicTacSection(r.Object("ticTac"));
            WallRun = new WallRunSection(r.Object("wallRun"));
            PoleVault = new PoleVaultSection(r.Object("poleVault"));
            Grapple = new GrappleSection(r.Object("grapple"));
            r.RejectUnknown();
            Values = r.Log;
        }

        /// <summary>Parses movement.json text. Throws <see cref="MovementConfigException"/> on any contract violation.</summary>
        public static MovementConfig Parse(string json, string sourceName = "movement.json")
        {
            object root;
            try
            {
                root = StrictJson.Parse(json);
            }
            catch (FormatException e)
            {
                throw new MovementConfigException($"{sourceName}: not valid JSON ({e.Message})", e);
            }
            if (!(root is Dictionary<string, object> dict))
                throw new MovementConfigException($"{sourceName}: the top level must be an object");
            var log = new SortedDictionary<string, object>(StringComparer.Ordinal);
            return new MovementConfig(new Reader(dict, "", sourceName, log));
        }

        /// <summary><c>speeds</c> section.</summary>
        public sealed class SpeedsSection
        {
            public readonly float Walk;
            public readonly float Jog;
            public readonly float Run;
            public readonly float Sprint;
            public readonly float Shimmy;
            public readonly float Rung;
            public readonly float Stud;
            public readonly float FreeClimb;
            public readonly float Pole;
            public readonly float Overhang;

            internal SpeedsSection(Reader r)
            {
                Walk = r.Number("walk");
                Jog = r.Number("jog");
                Run = r.Number("run");
                Sprint = r.Number("sprint");
                Shimmy = r.Number("shimmy");
                Rung = r.Number("rung");
                Stud = r.Number("stud");
                FreeClimb = r.Number("freeClimb");
                Pole = r.Number("pole");
                Overhang = r.Number("overhang");
                r.RejectUnknown();
            }
        }

        /// <summary><c>jump</c> section.</summary>
        public sealed class JumpSection
        {
            public readonly float StandingHeight;
            public readonly float StandingDistance;
            public readonly float RunningHeight;
            public readonly float RunningDistance;
            public readonly float SprintDistance;
            public readonly float PrecisionDamping;
            public readonly float CoyoteMs;
            public readonly float BufferMs;
            public readonly float LedgeCatchRadius;

            internal JumpSection(Reader r)
            {
                StandingHeight = r.Number("standingHeight");
                StandingDistance = r.Number("standingDistance");
                RunningHeight = r.Number("runningHeight");
                RunningDistance = r.Number("runningDistance");
                SprintDistance = r.Number("sprintDistance");
                PrecisionDamping = r.Number("precisionDamping");
                CoyoteMs = r.Number("coyoteMs");
                BufferMs = r.Number("bufferMs");
                LedgeCatchRadius = r.Number("ledgeCatchRadius");
                r.RejectUnknown();
            }
        }

        /// <summary><c>verticals</c> section.</summary>
        public sealed class VerticalsSection
        {
            public readonly float StepUp;
            public readonly float HopOver;
            public readonly float Vault;
            public readonly float Mantle;
            public readonly float VaultMaxDepth;
            public readonly float HopMaxDepth;

            internal VerticalsSection(Reader r)
            {
                StepUp = r.Number("stepUp");
                HopOver = r.Number("hopOver");
                Vault = r.Number("vault");
                Mantle = r.Number("mantle");
                VaultMaxDepth = r.Number("vaultMaxDepth");
                HopMaxDepth = r.Number("hopMaxDepth");
                r.RejectUnknown();
            }
        }

        /// <summary><c>landing</c> section.</summary>
        public sealed class LandingSection
        {
            public readonly float Soft;
            public readonly float Roll;
            public readonly float Hard;
            public readonly float SoftSurfaceTierBonus;

            internal LandingSection(Reader r)
            {
                Soft = r.Number("soft");
                Roll = r.Number("roll");
                Hard = r.Number("hard");
                SoftSurfaceTierBonus = r.Number("softSurfaceTierBonus");
                r.RejectUnknown();
            }
        }

        /// <summary><c>slopes</c> section.</summary>
        public sealed class SlopesSection
        {
            public readonly float RunMaxDeg;
            public readonly float SlideMinDeg;
            public readonly float SlideMaxDeg;

            internal SlopesSection(Reader r)
            {
                RunMaxDeg = r.Number("runMaxDeg");
                SlideMinDeg = r.Number("slideMinDeg");
                SlideMaxDeg = r.Number("slideMaxDeg");
                r.RejectUnknown();
            }
        }

        /// <summary><c>reach</c> section.</summary>
        public sealed class ReachSection
        {
            public readonly float LedgeToLedge;
            public readonly float HoldReach;
            public readonly float SlipChanceAtMaxReach;

            internal ReachSection(Reader r)
            {
                LedgeToLedge = r.Number("ledgeToLedge");
                HoldReach = r.Number("holdReach");
                SlipChanceAtMaxReach = r.Number("slipChanceAtMaxReach");
                r.RejectUnknown();
            }
        }

        /// <summary><c>assist</c> section.</summary>
        public sealed class AssistSection
        {
            public readonly float CoyoteMs;
            public readonly float JumpBonus;
            public readonly bool SlipsOff;
            public readonly bool AutoGrab;

            internal AssistSection(Reader r)
            {
                CoyoteMs = r.Number("coyoteMs");
                JumpBonus = r.Number("jumpBonus");
                SlipsOff = r.Flag("slipsOff");
                AutoGrab = r.Flag("autoGrab");
                r.RejectUnknown();
            }
        }

        /// <summary><c>dive</c> section.</summary>
        public sealed class DiveSection
        {
            public readonly float MinSpeed;
            public readonly float DistanceA;
            public readonly float RollAboveA;

            internal DiveSection(Reader r)
            {
                MinSpeed = r.Number("minSpeed");
                DistanceA = r.Number("distanceA");
                RollAboveA = r.Number("rollAboveA");
                r.RejectUnknown();
            }
        }

        /// <summary><c>ticTac</c> section.</summary>
        public sealed class TicTacSection
        {
            public readonly float ReboundHeightA;
            public readonly float ReboundDistanceA;
            public readonly float MaxChain;

            internal TicTacSection(Reader r)
            {
                ReboundHeightA = r.Number("reboundHeightA");
                ReboundDistanceA = r.Number("reboundDistanceA");
                MaxChain = r.Number("maxChain");
                r.RejectUnknown();
            }
        }

        /// <summary><c>wallRun</c> section.</summary>
        public sealed class WallRunSection
        {
            public readonly float MinWallRunA;
            public readonly float MaxDurationSec;
            public readonly float Speed;
            public readonly float MinEntrySpeed;
            public readonly float GravityDampen;

            internal WallRunSection(Reader r)
            {
                MinWallRunA = r.Number("minWallRunA");
                MaxDurationSec = r.Number("maxDurationSec");
                Speed = r.Number("speed");
                MinEntrySpeed = r.Number("minEntrySpeed");
                GravityDampen = r.Number("gravityDampen");
                r.RejectUnknown();
            }
        }

        /// <summary><c>poleVault</c> section.</summary>
        public sealed class PoleVaultSection
        {
            public readonly float PlantWindowSec;
            public readonly float MinRunSpeed;
            public readonly float MaxGapA;
            public readonly float MaxHeightA;

            internal PoleVaultSection(Reader r)
            {
                PlantWindowSec = r.Number("plantWindowSec");
                MinRunSpeed = r.Number("minRunSpeed");
                MaxGapA = r.Number("maxGapA");
                MaxHeightA = r.Number("maxHeightA");
                r.RejectUnknown();
            }
        }

        /// <summary><c>grapple</c> section.</summary>
        public sealed class GrappleSection
        {
            public readonly float ReachA;
            public readonly float SwingSpeed;
            public readonly float SwingMaxArcDeg;
            public readonly float AscendSpeed;
            public readonly float RappelSpeed;
            public readonly float DeploySec;
            public readonly float ReelSec;
            public readonly float AnchorMinLedgeA;
            public readonly float SnapAssistA;

            internal GrappleSection(Reader r)
            {
                ReachA = r.Number("reachA");
                SwingSpeed = r.Number("swingSpeed");
                SwingMaxArcDeg = r.Number("swingMaxArcDeg");
                AscendSpeed = r.Number("ascendSpeed");
                RappelSpeed = r.Number("rappelSpeed");
                DeploySec = r.Number("deploySec");
                ReelSec = r.Number("reelSec");
                AnchorMinLedgeA = r.Number("anchorMinLedgeA");
                SnapAssistA = r.Number("snapAssistA");
                r.RejectUnknown();
            }
        }

        internal sealed class Reader
        {
            readonly Dictionary<string, object> _data;
            readonly string _prefix;
            readonly string _source;
            readonly HashSet<string> _seen = new HashSet<string>(StringComparer.Ordinal);
            public readonly SortedDictionary<string, object> Log;

            public Reader(
                Dictionary<string, object> data,
                string prefix,
                string source,
                SortedDictionary<string, object> log
            )
            {
                _data = data;
                _prefix = prefix;
                _source = source;
                Log = log;
            }

            string PathOf(string key) => _prefix.Length == 0 ? key : _prefix + "." + key;

            object Take(string key)
            {
                _seen.Add(key);
                if (!_data.TryGetValue(key, out var value))
                    throw new MovementConfigException(
                        $"{_source}: missing required key '{PathOf(key)}' (Movement Bible §10)"
                    );
                return value;
            }

            public float Number(string key)
            {
                var value = Take(key);
                if (!(value is double d))
                    throw new MovementConfigException(
                        $"{_source}: key '{PathOf(key)}' must be a number"
                    );
                Log[PathOf(key)] = d;
                return (float)d;
            }

            public bool Flag(string key)
            {
                var value = Take(key);
                if (!(value is bool b))
                    throw new MovementConfigException(
                        $"{_source}: key '{PathOf(key)}' must be true or false"
                    );
                Log[PathOf(key)] = b;
                return b;
            }

            public Reader Object(string key)
            {
                var value = Take(key);
                if (!(value is Dictionary<string, object> dict))
                    throw new MovementConfigException(
                        $"{_source}: key '{PathOf(key)}' must be an object"
                    );
                return new Reader(dict, PathOf(key), _source, Log);
            }

            public void RejectUnknown()
            {
                foreach (var key in _data.Keys)
                {
                    if (!_seen.Contains(key))
                        throw new MovementConfigException(
                            $"{_source}: unknown key '{PathOf(key)}' (not in Movement Bible §10; "
                                + "new keys need an AUTH design-change)"
                        );
                }
            }
        }

        /// <summary>Invariant-culture text of a value, for messages and fixtures.</summary>
        public static string Format(object value) =>
            value is bool b
                ? (b ? "true" : "false")
                : Convert
                    .ToDouble(value, CultureInfo.InvariantCulture)
                    .ToString("R", CultureInfo.InvariantCulture);
    }
}
