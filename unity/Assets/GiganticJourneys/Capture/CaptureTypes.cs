using UnityEngine;

namespace GiganticJourneys.Capture
{
    /// <summary>The two guided modes, chosen by the illustrated toggle (DESIGN_SYSTEM §6).</summary>
    public enum CaptureMode
    {
        /// <summary>Room walkthrough: chest-height arc around the space.</summary>
        Room,

        /// <summary>Tabletop orbital: slow circle at two heights around the build.</summary>
        Tabletop,
    }

    /// <summary>ARKit camera tracking state (ARCamera.trackingState), platform-neutral.</summary>
    public enum TrackingQuality
    {
        /// <summary>Tracking is good.</summary>
        Normal,

        /// <summary>Tracking is degraded (fast motion, few features, relocalizing).</summary>
        Limited,

        /// <summary>No pose.</summary>
        NotAvailable,
    }

    /// <summary>
    /// One recorded camera frame as the capture logic sees it. The platform adapter (ARKit via AR
    /// Foundation, not yet in the project) fills it from the AR frame and a downsampled luma image;
    /// tests and the Editor use <see cref="SyntheticCapture"/>.
    /// </summary>
    public readonly struct CaptureFrame
    {
        /// <summary>Video frame index.</summary>
        public readonly int Index;

        /// <summary>Seconds since recording started (monotonic; pauses excluded by the caller).</summary>
        public readonly double Time;

        /// <summary>Camera position, ARKit world space (metres, +Y up).</summary>
        public readonly Vector3 Position;

        /// <summary>Camera rotation, ARKit world space. The camera looks along rotation * forward.</summary>
        public readonly Quaternion Rotation;

        /// <summary>Tracking state for this frame.</summary>
        public readonly TrackingQuality Tracking;

        /// <summary>Variance of the Laplacian of the downsampled luma (<see cref="FrameMetrics"/>).</summary>
        public readonly float Sharpness;

        /// <summary>Mean luma, 0–1.</summary>
        public readonly float Luma;

        /// <summary>True when the frame carries LiDAR depth.</summary>
        public readonly bool HasDepth;

        /// <summary>Creates a frame.</summary>
        public CaptureFrame(
            int index,
            double time,
            Vector3 position,
            Quaternion rotation,
            TrackingQuality tracking,
            float sharpness,
            float luma,
            bool hasDepth
        )
        {
            Index = index;
            Time = time;
            Position = position;
            Rotation = rotation;
            Tracking = tracking;
            Sharpness = sharpness;
            Luma = luma;
            HasDepth = hasDepth;
        }

        /// <summary>The viewing direction (unit).</summary>
        public Vector3 Forward => Rotation * Vector3.forward;
    }

    /// <summary>Pinhole intrinsics at capture resolution (pixels).</summary>
    public readonly struct CameraIntrinsics
    {
        /// <summary>Focal length x.</summary>
        public readonly float Fx;

        /// <summary>Focal length y.</summary>
        public readonly float Fy;

        /// <summary>Principal point x.</summary>
        public readonly float Cx;

        /// <summary>Principal point y.</summary>
        public readonly float Cy;

        /// <summary>Creates intrinsics.</summary>
        public CameraIntrinsics(float fx, float fy, float cx, float cy)
        {
            Fx = fx;
            Fy = fy;
            Cx = cx;
            Cy = cy;
        }
    }
}
