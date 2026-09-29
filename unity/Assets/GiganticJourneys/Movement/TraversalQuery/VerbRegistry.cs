using System;
using System.Collections.Generic;

namespace GiganticJourneys.Movement.Query
{
    /// <summary>
    /// The traversal query's verb resolution (Bible §2): every registered <see cref="IVerbProvider"/>
    /// may propose a verb for the frame and the highest <see cref="VerbPriority"/> wins; among equal
    /// priorities the later-registered provider wins, so an added provider can specialise a core one.
    /// </summary>
    public sealed class VerbRegistry
    {
        readonly List<IVerbProvider> _providers = new List<IVerbProvider>();

        public IReadOnlyList<IVerbProvider> Providers => _providers;

        public void Register(IVerbProvider provider)
        {
            if (provider == null)
                throw new ArgumentNullException(nameof(provider));
            foreach (var p in _providers)
            {
                if (p.Id == provider.Id)
                    throw new InvalidOperationException(
                        $"verb provider '{provider.Id}' is already registered"
                    );
            }
            _providers.Add(provider);
        }

        public bool Unregister(string id) => _providers.RemoveAll(p => p.Id == id) > 0;

        public string Resolve(in VerbContext context, MovementConfig config)
        {
            string best = null;
            var bestPriority = VerbPriority.Locomotion;
            foreach (var provider in _providers)
            {
                if (
                    !provider.TryPropose(context, config, out var proposal)
                    || proposal.Verb == null
                )
                    continue;
                if (best == null || proposal.Priority >= bestPriority)
                {
                    best = proposal.Verb;
                    bestPriority = proposal.Priority;
                }
            }
            return best ?? Verbs.Idle;
        }
    }

    /// <summary>
    /// M0 locomotion verbs (Bible §3.1, §3.3, §3.4): idle/walk/jog/run/sprint on the ground, the
    /// standing/running/sprint jump for the whole committed arc, and otherwise airborne, then fall
    /// after 0.35 s in the air (walking off an edge, or dropping below the take-off height).
    /// No contact verbs (M1).
    /// </summary>
    public sealed class LocomotionVerbProvider : IVerbProvider
    {
        public string Id => "gj.locomotion";

        public bool TryPropose(
            in VerbContext context,
            MovementConfig config,
            out VerbProposal proposal
        )
        {
            string verb;
            if (context.JumpFired)
                verb = JumpVerb(context.TakeoffGait);
            else if (
                !context.Grounded
                && context.ActiveJump != null
                && context.AirborneSeconds <= context.ActiveJumpAirTime
            )
                verb = context.ActiveJump; // the committed arc keeps its verb until it lands or overruns
            else if (!context.Grounded)
                verb =
                    context.AirborneSeconds > ProvisionalTuning.Intent.FallAfterSec
                        ? Verbs.Fall
                        : Verbs.Airborne;
            else
                verb = GroundVerb(context.Gait);
            proposal = new VerbProposal(verb, VerbPriority.Locomotion);
            return true;
        }

        /// <summary>Standing jump from idle/walk (speed below jog), running jump at jog/run, sprint jump when sprinting.</summary>
        public static string JumpVerb(Gait takeoffGait)
        {
            switch (takeoffGait)
            {
                case Gait.Sprint:
                    return Verbs.SprintJump;
                case Gait.Jog:
                case Gait.Run:
                    return Verbs.RunningJump;
                default:
                    return Verbs.StandingJump;
            }
        }

        public static string GroundVerb(Gait gait)
        {
            switch (gait)
            {
                case Gait.Walk:
                    return Verbs.Walk;
                case Gait.Jog:
                    return Verbs.Jog;
                case Gait.Run:
                    return Verbs.Run;
                case Gait.Sprint:
                    return Verbs.Sprint;
                default:
                    return Verbs.Idle;
            }
        }

        /// <summary>Jump height and distance in A for a jump verb (movement.json jump.*).</summary>
        public static void JumpShape(
            string verb,
            MovementConfig config,
            out float height,
            out float distance
        )
        {
            if (verb == Verbs.SprintJump)
            {
                height = config.Jump.RunningHeight;
                distance = config.Jump.SprintDistance;
            }
            else if (verb == Verbs.RunningJump)
            {
                height = config.Jump.RunningHeight;
                distance = config.Jump.RunningDistance;
            }
            else
            {
                height = config.Jump.StandingHeight;
                distance = config.Jump.StandingDistance;
            }
        }
    }
}
