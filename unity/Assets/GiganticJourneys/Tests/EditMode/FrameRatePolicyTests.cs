using System.Reflection;
using NUnit.Framework;
using UnityEngine;

namespace GiganticJourneys.Tests
{
    public class FrameRatePolicyTests
    {
        [Test]
        public void MobileTargetsSixtyFps()
        {
            Assert.AreEqual(60, FrameRatePolicy.MobileTargetFps);
            Assert.AreEqual(60, FrameRatePolicy.TargetFor(true));
        }

        [Test]
        public void EditorAndDesktopKeepThePlatformDefault()
        {
            Assert.IsNull(FrameRatePolicy.TargetFor(false));
        }

        [Test]
        public void AppliedBeforeTheFirstSceneLoads()
        {
            var apply = typeof(FrameRatePolicy).GetMethod(
                "Apply",
                BindingFlags.Static | BindingFlags.NonPublic
            );
            Assert.IsNotNull(apply, "FrameRatePolicy.Apply missing");
            var attr = apply.GetCustomAttribute<RuntimeInitializeOnLoadMethodAttribute>();
            Assert.IsNotNull(attr, "Apply is not a RuntimeInitializeOnLoadMethod");
            Assert.AreEqual(RuntimeInitializeLoadType.BeforeSceneLoad, attr.loadType);
        }
    }
}
