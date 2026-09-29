using System;
using System.IO;
using GiganticJourneys.Capture;
using NUnit.Framework;
using UnityEngine;

namespace GiganticJourneys.Tests.Capture
{
    /// <summary>
    /// M1-CAPT-01 AT-1/AT-4: the bundle writer produces the capture → reconstruction contract
    /// (services/reconstruction/bundle/capture_bundle.schema.json), deterministically, with no
    /// location. The golden bundles under services/reconstruction/bundle/fixtures/ are this writer's
    /// output; the Python validator (services/reconstruction/tests/test_capture_bundle.py) checks the
    /// same files against the schema, which ties the C# writer to the contract. Regenerate them with
    /// GJ_WRITE_CAPTURE_GOLDEN=1 after an intended change.
    /// </summary>
    public class CaptureBundleWriterTests
    {
        private static CaptureBundleInfo Info(bool lidar) =>
            new CaptureBundleInfo
            {
                ScanId = "0b6f7c1e-4d2a-4c1b-9e3f-5a6b7c8d9e0f",
                CapturedOn = new DateTime(2026, 9, 29, 3, 14, 15, DateTimeKind.Local),
                DeviceModel = "iPhone16,1",
                HasLidar = lidar,
                VideoContainer = "mov",
                VideoCodec = "hevc",
                VideoWidth = 1920,
                VideoHeight = 1440,
                VideoFps = 30f,
                VideoFrameCount = 2400,
                ImageWidth = 1920,
                ImageHeight = 1440,
                Intrinsics = new CameraIntrinsics(1450.5f, 1450.5f, 960.2f, 719.8f),
                Gravity = new Vector3(0f, -1f, 0f),
                DepthWidth = 256,
                DepthHeight = 192,
            };

        private static CaptureSession Captured(CaptureMode mode, bool lidar)
        {
            var session = CaptureSessionTests.Recording(mode);
            // 12 s at 15 fps, half the sweep (room: three of six heights; tabletop: the low circle),
            // one second of tracking loss: a small, realistic partial capture.
            var synth = new SyntheticCapture
            {
                Seconds = 12f,
                Fps = 15f,
                SweepFraction = 0.5f,
                Depth = lidar,
                TrackingLossWindow = new Vector2(5f, 6f),
            };
            CaptureSessionTests.Feed(session, synth.Generate(mode));
            return session;
        }

        [Test]
        public void ManifestHasEveryContractSectionAndNoLocation()
        {
            string manifest = CaptureBundleWriter.Manifest(
                Captured(CaptureMode.Room, lidar: true),
                Info(lidar: true)
            );
            foreach (
                var key in new[]
                {
                    "\"schema_version\": \"1.0\"",
                    "\"scan_id\"",
                    "\"mode\": \"room\"",
                    "\"source\": \"gj-app\"",
                    "\"captured_on\": \"2026-09-29\"",
                    "\"device\"",
                    "\"readiness\"",
                    "\"coverage\"",
                    "\"map\"",
                    "\"video\"",
                    "\"camera\"",
                    "\"intrinsics\"",
                    "\"world\"",
                    "\"gravity\"",
                    "\"frames\"",
                    "\"depth\": {",
                    "\"passes\"",
                    "\"metadata_stripped\": true",
                    "\"location_recorded\": false",
                }
            )
            {
                Assert.That(manifest, Does.Contain(key), key);
            }

            string lower = manifest.ToLowerInvariant().Replace("location_recorded", string.Empty);
            foreach (
                var banned in new[]
                {
                    "gps",
                    "latitude",
                    "longitude",
                    "altitude",
                    "location",
                    "exif",
                    "03:14",
                }
            )
            {
                Assert.That(lower, Does.Not.Contain(banned), banned);
            }
        }

        [Test]
        public void NoLidar_WritesNullDepthAndNoDepthFrames()
        {
            var session = Captured(CaptureMode.Tabletop, lidar: false);
            string manifest = CaptureBundleWriter.Manifest(session, Info(lidar: false));
            Assert.That(manifest, Does.Contain("\"depth\": null"));
            Assert.That(
                CaptureBundleWriter.Frames(session, Info(lidar: false)),
                Does.Not.Contain("\"depth\":true")
            );
        }

        [Test]
        public void FramesAreOneLinePerFrameWithARigidPose()
        {
            var session = Captured(CaptureMode.Room, lidar: false);
            string[] lines = CaptureBundleWriter
                .Frames(session, Info(false))
                .TrimEnd('\n')
                .Split('\n');
            Assert.That(lines.Length, Is.EqualTo(session.Frames.Count));
            Assert.That(lines[0], Does.StartWith("{\"i\":0,\"t\":0,\"pose\":["));
            Assert.That(lines[0], Does.EndWith("}"));
            Assert.That(lines[82], Does.Contain("\"tracking\":\"limited\"")); // t = 5.47 s
        }

        [Test]
        public void OutputIsDeterministic()
        {
            var a = Captured(CaptureMode.Room, lidar: true);
            var b = Captured(CaptureMode.Room, lidar: true);
            Assert.That(
                CaptureBundleWriter.Manifest(a, Info(true)),
                Is.EqualTo(CaptureBundleWriter.Manifest(b, Info(true)))
            );
            Assert.That(
                CaptureBundleWriter.Frames(a, Info(true)),
                Is.EqualTo(CaptureBundleWriter.Frames(b, Info(true)))
            );
        }

        [Test]
        public void EmptyCaptureCannotBeBundled()
        {
            var session = new CaptureSession(CaptureMode.Room, firstRun: false);
            Assert.Throws<InvalidOperationException>(() =>
                CaptureBundleWriter.Manifest(session, Info(false))
            );
        }

        [TestCase("synthetic-room-lidar", CaptureMode.Room, true)]
        [TestCase("synthetic-tabletop", CaptureMode.Tabletop, false)]
        public void MatchesTheGoldenBundle(string name, CaptureMode mode, bool lidar)
        {
            string dir = Path.GetFullPath(
                Path.Combine(
                    Application.dataPath,
                    "..",
                    "..",
                    "services",
                    "reconstruction",
                    "bundle",
                    "fixtures",
                    name
                )
            );
            var session = Captured(mode, lidar);
            if (Environment.GetEnvironmentVariable("GJ_WRITE_CAPTURE_GOLDEN") == "1")
            {
                CaptureBundleWriter.Write(dir, session, Info(lidar));
                Assert.Pass($"golden bundle written to {dir}");
            }

            if (!File.Exists(Path.Combine(dir, "manifest.json")))
            {
                Assert.Ignore(
                    $"golden bundle not found at {dir} (Unity project outside the repo checkout)"
                );
            }

            Assert.That(
                CaptureBundleWriter.Manifest(session, Info(lidar)),
                Is.EqualTo(File.ReadAllText(Path.Combine(dir, "manifest.json")))
            );
            Assert.That(
                CaptureBundleWriter.Frames(session, Info(lidar)),
                Is.EqualTo(File.ReadAllText(Path.Combine(dir, "frames.jsonl")))
            );
        }
    }
}
