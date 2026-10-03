using UnityEngine;

namespace GiganticJourneys
{
    /// <summary>
    /// Frame-rate cap for the player (SPEC §6: 60 fps target on current iPhones, 30 fps
    /// target on older ones through automatic quality tiering). iOS defaults
    /// Application.targetFrameRate to -1, which Unity runs at 30 fps on mobile, so without
    /// this the 60 fps target is unreachable on every device (M0-UNITY-04 device report,
    /// iPhone14,7: fps_p50 30, target_frame_rate -1). The cap is 60; quality tiering, not
    /// this cap, brings older devices toward 30. QualitySettings.vSyncCount is ignored on
    /// iOS. The Editor and desktop players are left alone so PlayMode tests run unthrottled.
    /// </summary>
    public static class FrameRatePolicy
    {
        public const int MobileTargetFps = 60;

        /// <summary>The target to apply, or null to leave the platform default.</summary>
        public static int? TargetFor(bool isMobilePlatform) =>
            isMobilePlatform ? MobileTargetFps : (int?)null;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Apply()
        {
            var target = TargetFor(Application.isMobilePlatform);
            if (target.HasValue)
                Application.targetFrameRate = target.Value;
        }
    }
}
