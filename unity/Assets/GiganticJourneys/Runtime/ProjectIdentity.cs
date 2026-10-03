namespace GiganticJourneys
{
    /// <summary>
    /// Store identity of the app. The single source for the values that
    /// Assets/Editor/ProjectSetup.cs writes into PlayerSettings and that the
    /// EditMode smoke test checks (unity/README.md, ticket M0-UNITY-01).
    /// </summary>
    public static class ProjectIdentity
    {
        public const string BundleId = "com.sparkforgelabs.giganticjourneys";
        public const string ProductName = "Gigantic Journeys";
        public const string CompanyName = "SparkForge Labs";

        // The playable movement scene boots first (touch stick, jump pad, follow camera) so
        // TestFlight builds open into something the Owner can play (2026-10-02).
        public const string BootScenePath = "Assets/Scenes/MovementTest.unity";
    }
}
