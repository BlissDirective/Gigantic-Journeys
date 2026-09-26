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
        public const string BootScenePath = "Assets/Scenes/SampleScene.unity";
    }
}
