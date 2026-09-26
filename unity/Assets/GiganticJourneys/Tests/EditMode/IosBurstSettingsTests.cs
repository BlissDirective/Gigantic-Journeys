using GiganticJourneys.EditorTools.Build;
using NUnit.Framework;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// M3-UNITY-01: the iOS Burst state is explicit and committed (ENABLED), and
    /// only the Linux compile-check export turns it off, for that build only.
    /// </summary>
    public class IosBurstSettingsTests
    {
        [Test]
        public void IosBurstIsCommittedEnabled()
        {
            Assert.AreEqual(
                true,
                IosBurstBuildHook.CommittedEnabled(),
                $"{IosBurstBuildHook.SettingsPath} must exist with \"EnableBurstCompilation\": true"
            );
        }

        [Test]
        public void DisableFlagIsOptInAndParsed()
        {
            Assert.IsFalse(IosBurstBuildHook.DisableRequested(new[] { "Unity", "-batchmode" }));
            Assert.IsTrue(
                IosBurstBuildHook.DisableRequested(
                    new[] { "Unity", "-batchmode", IosBurstBuildHook.DisableFlag }
                )
            );
            Assert.AreEqual(
                false,
                IosBurstBuildHook.ReadEnabled("{\"EnableBurstCompilation\": false}")
            );
            Assert.IsNull(IosBurstBuildHook.ReadEnabled("{}"));
        }
    }
}
