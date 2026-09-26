using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace GiganticJourneys.Tests
{
    public class RuntimeSmokeTests
    {
        [UnityTest]
        public IEnumerator PlayerLoopAdvancesAFrame()
        {
            var go = new GameObject("smoke");
            var start = Time.frameCount;
            yield return null;
            Assert.Greater(Time.frameCount, start);
            Assert.IsTrue(go != null);
            Object.Destroy(go);
        }
    }
}
