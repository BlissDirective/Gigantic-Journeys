namespace GiganticJourneys.Capture
{
    /// <summary>
    /// Cheap per-frame image metrics on a downsampled 8-bit luma buffer (e.g. the Y plane of the
    /// ARKit capture image, box-filtered to ~160x120). Allocation-free.
    /// </summary>
    public static class FrameMetrics
    {
        /// <summary>
        /// Variance of the 4-neighbour Laplacian over the interior pixels: the standard focus measure
        /// (Pech-Pacheco et al. 2000). Higher is sharper; motion blur drives it towards 0.
        /// </summary>
        public static float LaplacianVariance(byte[] luma, int width, int height)
        {
            if (luma == null || width < 3 || height < 3 || luma.Length < width * height)
            {
                return 0f;
            }

            double sum = 0;
            double sumSq = 0;
            int n = 0;
            for (int y = 1; y < height - 1; y++)
            {
                int row = y * width;
                for (int x = 1; x < width - 1; x++)
                {
                    int i = row + x;
                    int lap =
                        luma[i - 1] + luma[i + 1] + luma[i - width] + luma[i + width] - 4 * luma[i];
                    sum += lap;
                    sumSq += (double)lap * lap;
                    n++;
                }
            }

            double mean = sum / n;
            return (float)(sumSq / n - mean * mean);
        }

        /// <summary>Mean luma normalised to 0–1.</summary>
        public static float MeanLuma(byte[] luma, int width, int height)
        {
            int count = width * height;
            if (luma == null || count <= 0 || luma.Length < count)
            {
                return 0f;
            }

            long sum = 0;
            for (int i = 0; i < count; i++)
            {
                sum += luma[i];
            }

            return sum / (255f * count);
        }
    }
}
