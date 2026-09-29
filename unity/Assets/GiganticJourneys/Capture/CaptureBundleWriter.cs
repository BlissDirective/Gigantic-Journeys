using System;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEngine;

namespace GiganticJourneys.Capture
{
    /// <summary>Facts about the recording the session does not know (filled by the platform adapter).</summary>
    public sealed class CaptureBundleInfo
    {
        /// <summary>Random UUIDv4 minted on device (lower-case, hyphenated).</summary>
        public string ScanId;

        /// <summary>Calendar date only; the time and time zone are never recorded.</summary>
        public DateTime CapturedOn;

        /// <summary>Hardware model identifier (e.g. "iPhone16,1"); never the device name. Null if unknown.</summary>
        public string DeviceModel;

        /// <summary>True when the device has LiDAR (depth frames are written only then).</summary>
        public bool HasLidar;

        /// <summary>"mov" or "mp4".</summary>
        public string VideoContainer = "mov";

        /// <summary>"hevc" or "h264".</summary>
        public string VideoCodec = "hevc";

        /// <summary>Coded frame width.</summary>
        public int VideoWidth;

        /// <summary>Coded frame height.</summary>
        public int VideoHeight;

        /// <summary>Frames per second.</summary>
        public float VideoFps;

        /// <summary>Frames in the video file.</summary>
        public int VideoFrameCount;

        /// <summary>Capture image width (intrinsics refer to it).</summary>
        public int ImageWidth;

        /// <summary>Capture image height.</summary>
        public int ImageHeight;

        /// <summary>Pinhole intrinsics at capture resolution.</summary>
        public CameraIntrinsics Intrinsics;

        /// <summary>Mean gravity direction in world space (unit; ARKit gravity alignment gives -Y).</summary>
        public Vector3 Gravity = Vector3.down;

        /// <summary>LiDAR depth map width (ignored without LiDAR).</summary>
        public int DepthWidth;

        /// <summary>LiDAR depth map height (ignored without LiDAR).</summary>
        public int DepthHeight;
    }

    /// <summary>
    /// Writes the capture bundle's manifest.json and frames.jsonl (the capture → reconstruction
    /// contract, services/reconstruction/bundle/capture_bundle.schema.json v1.0). Invariant culture,
    /// fixed field order and rounding, so the same session always produces the same bytes.
    /// <para>Privacy (AT-4): nothing here can write a location: the manifest has no field for one,
    /// the date carries no time or zone, and the device is a model identifier. Stripping GPS/EXIF from
    /// the video itself is the native recorder's job (it writes no metadata track); the server
    /// re-verifies (SECURITY_CHECKLIST §4.4).</para>
    /// </summary>
    public static class CaptureBundleWriter
    {
        /// <summary>The bundle schema version this writer produces.</summary>
        public const string SchemaVersion = "1.0";

        /// <summary>Writes manifest.json and frames.jsonl into <paramref name="directory"/> (created if needed).</summary>
        public static void Write(string directory, CaptureSession session, CaptureBundleInfo info)
        {
            Directory.CreateDirectory(directory);
            File.WriteAllText(
                Path.Combine(directory, "manifest.json"),
                Manifest(session, info),
                new UTF8Encoding(false)
            );
            File.WriteAllText(
                Path.Combine(directory, "frames.jsonl"),
                Frames(session, info),
                new UTF8Encoding(false)
            );
        }

        /// <summary>The manifest.json text.</summary>
        public static string Manifest(CaptureSession session, CaptureBundleInfo info)
        {
            if (session.Frames.Count == 0)
            {
                throw new InvalidOperationException("cannot bundle a capture with no frames");
            }

            var frames = session.Frames;
            var readiness = session.Readiness;
            var map = session.Coverage;
            int accepted = 0;
            int depthFrames = 0;
            for (int i = 0; i < frames.Count; i++)
            {
                if (session.Accepted[i])
                {
                    accepted++;
                }

                if (info.HasLidar && frames[i].HasDepth)
                {
                    depthFrames++;
                }
            }

            float fraction = Round4(map.Fraction);
            Vector3 gravity = info.Gravity.normalized;
            var j = new JsonText();
            j.Open();
            j.Str("schema_version", SchemaVersion);
            j.Str("scan_id", info.ScanId);
            j.Str("mode", session.Mode == CaptureMode.Room ? "room" : "tabletop");
            j.Str("source", "gj-app");
            j.Str(
                "captured_on",
                info.CapturedOn.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture)
            );
            j.Open("device");
            j.StrOrNull("model", info.DeviceModel);
            j.Bool("lidar", info.HasLidar);
            j.Close();
            j.Num("duration_s", Math.Max(0.001f, Round4(session.ActiveSeconds)));
            j.Open("readiness");
            j.Num("score", Round4(readiness.Score));
            j.Str("source", "gj-app");
            j.Open("components");
            j.Num("coverage", fraction);
            j.Num("parallax", Round4(readiness.Parallax));
            j.Num("sharpness", Round4(readiness.Sharpness));
            j.Num("light", Round4(readiness.Light));
            j.Num("tracking", Round4(readiness.Tracking));
            j.Close();
            j.Str("weakest", readiness.WeakestId);
            j.Close();
            j.Open("coverage");
            j.Str(
                "summary",
                string.Format(
                    CultureInfo.InvariantCulture,
                    "{0} {1}: {2:0}% painted over {3} pass(es)",
                    session.Mode == CaptureMode.Room ? "room" : "tabletop",
                    map.Kind,
                    fraction * 100f,
                    session.Passes.Count
                )
            );
            j.Num("fraction", fraction);
            j.Int("passes", session.Passes.Count);
            j.Open("map");
            j.Str("kind", map.Kind);
            j.Int("azimuth_bins", map.AzimuthBins);
            j.Int("elevation_bins", map.ElevationBins);
            j.Num("elevation_min_deg", map.ElevationMinDeg);
            j.Num("elevation_max_deg", map.ElevationMaxDeg);
            j.StrArray("painted", map.PaintedRows());
            j.Close();
            j.Close();
            j.Open("video");
            j.Str("file", "video." + info.VideoContainer);
            j.Str("container", info.VideoContainer);
            j.Str("codec", info.VideoCodec);
            j.Int("width", info.VideoWidth);
            j.Int("height", info.VideoHeight);
            j.Num("fps", info.VideoFps);
            j.Int("frame_count", info.VideoFrameCount);
            j.Close();
            j.Open("camera");
            j.Int("image_width", info.ImageWidth);
            j.Int("image_height", info.ImageHeight);
            WriteIntrinsics(j, info.Intrinsics);
            j.Close();
            j.Open("world");
            j.Str("alignment", "gravity");
            j.NumArray("up", 0f, 1f, 0f);
            j.NumArray("gravity", Round4(gravity.x), Round4(gravity.y), Round4(gravity.z));
            j.Str("metric_scale", "arkit-metres");
            j.Close();
            j.Open("frames");
            j.Str("file", "frames.jsonl");
            j.Int("count", frames.Count);
            j.Int("accepted", accepted);
            j.Num("tracking_normal_fraction", Round4(session.Tracking.NormalFraction));
            j.Close();
            if (info.HasLidar && depthFrames > 0)
            {
                j.Open("depth");
                j.Str("dir", "depth");
                j.Str("format", "float16-le-metres");
                j.Int("width", info.DepthWidth);
                j.Int("height", info.DepthHeight);
                j.Int("count", depthFrames);
                j.Close();
            }
            else
            {
                j.Null("depth");
            }

            j.OpenArray("passes");
            foreach (var pass in session.Passes)
            {
                j.OpenItem();
                j.Int("first_frame", pass.FirstFrame);
                j.Int("last_frame", pass.LastFrame);
                j.Str("reason", pass.Reason);
                j.CloseItem();
            }

            j.CloseArray();
            j.Open("privacy");
            j.Bool("metadata_stripped", true);
            j.Bool("location_recorded", false);
            j.Close();
            j.Close();
            return j.ToString();
        }

        /// <summary>The frames.jsonl text (one compact JSON object per recorded frame).</summary>
        public static string Frames(CaptureSession session, CaptureBundleInfo info)
        {
            var sb = new StringBuilder();
            var frames = session.Frames;
            double t0 = frames.Count > 0 ? frames[0].Time : 0;
            for (int i = 0; i < frames.Count; i++)
            {
                var f = frames[i];
                Matrix4x4 m = Matrix4x4.TRS(f.Position, f.Rotation.normalized, Vector3.one);
                sb.Append("{\"i\":").Append(f.Index.ToString(CultureInfo.InvariantCulture));
                sb.Append(",\"t\":").Append(Fmt((float)Math.Max(0, f.Time - t0)));
                sb.Append(",\"pose\":[");
                for (int c = 0; c < 4; c++)
                {
                    for (int r = 0; r < 4; r++)
                    {
                        if (c + r > 0)
                        {
                            sb.Append(',');
                        }

                        sb.Append(Fmt(m[r, c]));
                    }
                }

                sb.Append("],\"tracking\":\"").Append(TrackingId(f.Tracking)).Append('"');
                sb.Append(",\"sharpness\":").Append(Fmt(Math.Max(0f, f.Sharpness)));
                sb.Append(",\"luma\":").Append(Fmt(Mathf.Clamp01(f.Luma)));
                sb.Append(",\"accepted\":").Append(session.Accepted[i] ? "true" : "false");
                sb.Append(",\"depth\":").Append(info.HasLidar && f.HasDepth ? "true" : "false");
                sb.Append("}\n");
            }

            return sb.ToString();
        }

        private static void WriteIntrinsics(JsonText j, CameraIntrinsics k)
        {
            j.Open("intrinsics");
            j.Num("fx", k.Fx);
            j.Num("fy", k.Fy);
            j.Num("cx", k.Cx);
            j.Num("cy", k.Cy);
            j.Close();
        }

        private static string TrackingId(TrackingQuality t) =>
            t == TrackingQuality.Normal ? "normal"
            : t == TrackingQuality.Limited ? "limited"
            : "not-available";

        private static float Round4(float v) => (float)Math.Round(v, 4);

        private static string Fmt(float v)
        {
            // -0 prints as "0"; six decimals keep poses within the validator's 1e-3 rigidity check.
            if (Math.Abs(v) < 5e-7f)
            {
                return "0";
            }

            return v.ToString("0.######", CultureInfo.InvariantCulture);
        }

        /// <summary>A tiny indented JSON writer (fixed key order, two-space indent, invariant numbers).</summary>
        private sealed class JsonText
        {
            private readonly StringBuilder _sb = new StringBuilder();
            private int _depth;
            private bool _first = true;

            public void Open(string key = null)
            {
                Key(key);
                _sb.Append('{');
                _depth++;
                _first = true;
            }

            public void Close()
            {
                _depth--;
                NewLine();
                _sb.Append('}');
                _first = false;
                if (_depth == 0)
                {
                    _sb.Append('\n');
                }
            }

            public void OpenArray(string key)
            {
                Key(key);
                _sb.Append('[');
                _depth++;
                _first = true;
            }

            public void CloseArray()
            {
                _depth--;
                NewLine();
                _sb.Append(']');
                _first = false;
            }

            public void OpenItem()
            {
                Key(null);
                _sb.Append('{');
                _depth++;
                _first = true;
            }

            public void CloseItem() => Close();

            public void Str(string key, string value)
            {
                Key(key);
                Quote(value);
            }

            public void StrOrNull(string key, string value)
            {
                if (value == null)
                {
                    Null(key);
                }
                else
                {
                    Str(key, value);
                }
            }

            public void Null(string key)
            {
                Key(key);
                _sb.Append("null");
            }

            public void Bool(string key, bool value)
            {
                Key(key);
                _sb.Append(value ? "true" : "false");
            }

            public void Int(string key, int value)
            {
                Key(key);
                _sb.Append(value.ToString(CultureInfo.InvariantCulture));
            }

            public void Num(string key, float value)
            {
                Key(key);
                _sb.Append(Fmt(value));
            }

            public void NumArray(string key, params float[] values)
            {
                Key(key);
                _sb.Append('[');
                for (int i = 0; i < values.Length; i++)
                {
                    _sb.Append(i == 0 ? string.Empty : ", ").Append(Fmt(values[i]));
                }

                _sb.Append(']');
            }

            public void StrArray(string key, string[] values)
            {
                OpenArray(key);
                foreach (var v in values)
                {
                    Key(null);
                    Quote(v);
                }

                CloseArray();
            }

            public override string ToString() => _sb.ToString();

            private void Key(string key)
            {
                if (_depth > 0)
                {
                    if (!_first)
                    {
                        _sb.Append(',');
                    }

                    NewLine();
                }

                _first = false;
                if (key != null)
                {
                    Quote(key);
                    _sb.Append(": ");
                }
            }

            private void NewLine()
            {
                _sb.Append('\n').Append(' ', 2 * _depth);
            }

            private void Quote(string s)
            {
                _sb.Append('"');
                foreach (char ch in s)
                {
                    switch (ch)
                    {
                        case '"':
                            _sb.Append("\\\"");
                            break;
                        case '\\':
                            _sb.Append("\\\\");
                            break;
                        default:
                            if (ch < 0x20)
                            {
                                _sb.Append("\\u")
                                    .Append(((int)ch).ToString("x4", CultureInfo.InvariantCulture));
                            }
                            else
                            {
                                _sb.Append(ch);
                            }

                            break;
                    }
                }

                _sb.Append('"');
            }
        }
    }
}
