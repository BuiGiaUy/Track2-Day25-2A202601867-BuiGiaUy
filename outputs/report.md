# NimbusAI — GPU Cost Optimization Report

**Period:** monthly  
**Baseline spend:** $27,133  
**Optimized spend:** $14,626  
**Projected savings:** $12,507  (**46%**)

## Savings by lever

| Lever | Savings (USD) |
|---|---|
| Inference (cascade/cache/batch) | $1,212 |
| Purchasing (spot/reserved) | $10,040 |
| Right-size util-lies | $655 |
| Kill idle GPUs | $600 |

## Sustainability

- Energy per query: 0.24 Wh
- Carbon per query: 0.091 gCO2e
- Cheapest+cleanest region: europe-north1

## Your Turn extensions

- **Cache economics:** observed equivalent cache reads = 3.14; cache is worthwhile = **True**.
- **Reasoning budget:** reasoning traffic = 201/2400 requests (8.4%), costing $1.40/day (16.5% of optimized cost) and 29787.7 Wh/day; normal traffic costs $7.09/day and 1887.6 Wh/day.
- **10% reasoning policy simulation:** estimated cost = $8.48/day, energy = 31675.3 Wh/day, modeled savings = 0.0% versus current optimized routing.
- **GPU-Util lie mechanism:** high utilization can reflect memory stalls or kernel/launch overhead rather than useful tensor computation; MFU is therefore the better cost-efficiency signal. Prioritize right-sizing the two high-util, low-MFU GPUs before buying more capacity.
- **Sustainability action:** prioritize the cleanest region when latency permits, because lower energy/carbon intensity reduces both emissions and electricity exposure; re-check June-2026 rates before production decisions.

_Figures are June-2026 as-of snapshots; re-baseline before acting._