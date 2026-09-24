# Spike datasets

Public datasets for the reconstruction spike **smoke test** — used to prove the
pipeline before any consented corpus or real user scan (SECURITY_CHECKLIST §6.5).

| Name | Use | Source |
|---|---|---|
| `mipnerf360` | Default smoke test (indoor + outdoor scenes) | Mip-NeRF 360 (Google research data) — fetched by `reconstruction.fetch_dataset` |
| Tanks and Temples | Larger-scene stress test | Official Tanks and Temples project page (download manually; check terms) |
| Deep Blending | Indoor-scene variety | Deep Blending project page (download manually; check terms) |

Fetch the default set inside the container:

```python
from pathlib import Path
from reconstruction.fetch_dataset import fetch

fetch("mipnerf360", Path("./data/mipnerf360"))
```

Then run the spike driver against an extracted scene folder:

```bash
python -m reconstruction.spike --images ./data/mipnerf360/<scene>/images \
    --scan-id smoke --trainer gsplat --sfm glomap --rate 1.0
```

After the public smoke test passes, switch `--images` to a consented corpus room
and `--source corpus`. Corpus scans are Owner-supplied and consented; real user
scans never go to a third party (ADR-0005 / AUTH #030).
