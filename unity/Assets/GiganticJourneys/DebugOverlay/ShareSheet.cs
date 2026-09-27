#if UNITY_IOS && !UNITY_EDITOR
using System.Runtime.InteropServices;
#endif

namespace GiganticJourneys.DebugTools
{
    /// <summary>
    /// Opens the iOS share sheet for a file (Plugins/iOS/GJShareSheet.mm).
    /// Elsewhere (Editor, desktop players) it is a no-op that returns false.
    /// </summary>
    public static class ShareSheet
    {
#if UNITY_IOS && !UNITY_EDITOR
        [DllImport("__Internal")]
        static extern void GJ_ShareFile(string path);
#endif

        public static bool Share(string path)
        {
#if UNITY_IOS && !UNITY_EDITOR
            GJ_ShareFile(path);
            return true;
#else
            return false;
#endif
        }
    }
}
