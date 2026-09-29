using System;

namespace GiganticJourneys.Movement
{
    /// <summary>
    /// Launch velocities for a committed jump (Bible §3.3) that peaks at <c>height</c> and lands
    /// <c>distance</c> away on level ground under gravity <c>g</c> (all in A units). No air control
    /// in v1: the arc is fixed at take-off.
    /// </summary>
    public readonly struct JumpBallistics
    {
        public readonly float VerticalSpeed;
        public readonly float HorizontalSpeed;
        public readonly float AirTime;

        JumpBallistics(float vertical, float horizontal, float airTime)
        {
            VerticalSpeed = vertical;
            HorizontalSpeed = horizontal;
            AirTime = airTime;
        }

        public static JumpBallistics Solve(float height, float distance, float gravity)
        {
            if (height <= 0f || gravity <= 0f || distance < 0f)
                throw new ArgumentOutOfRangeException(
                    nameof(height),
                    "height, gravity > 0 and distance >= 0"
                );
            // v^2 = 2 g h at the apex; the flight lasts twice the rise time.
            var vertical = (float)Math.Sqrt(2f * gravity * height);
            var airTime = 2f * vertical / gravity;
            return new JumpBallistics(vertical, distance / airTime, airTime);
        }
    }
}
