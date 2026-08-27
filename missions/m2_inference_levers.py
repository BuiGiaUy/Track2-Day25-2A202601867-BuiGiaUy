"""M2 — Inference Cost Levers: $/1M-token, batch x cache x cascade (deck §7).

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num
from finops import pricing, sustainability

# $/1M tokens (input, output) — illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}


def run(verbose: bool = True) -> dict:
    rows = load_csv("token_usage.csv")
    base_cost = opt_cost = 0.0
    total_tokens = 0
    cache_input_tokens = 0
    total_input_tokens = 0
    reasoning_cost = 0.0
    normal_cost = 0.0
    reasoning_wh = 0.0
    normal_wh = 0.0
    row_costs = []
    for r in rows:
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"]))
        is_batch = bool(int(num(r["is_batch"])))
        is_reasoning = bool(int(num(r["is_reasoning"])))
        total_tokens += inp + out
        total_input_tokens += inp
        cache_input_tokens += cached
        # BASELINE: naive deployment — everything on the large model, no cache, no batch
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)
        # OPTIMIZED: cascade (route_tier), prompt caching, batch API
        pin, pout = MODEL_PRICES[r["route_tier"]]
        row_opt_cost = pricing.request_cost(inp, out, pin, pout, cached_in=cached, batch=is_batch)
        opt_cost += row_opt_cost
        row_costs.append((row_opt_cost, is_reasoning, inp + out, r))
        if is_reasoning:
            reasoning_cost += row_opt_cost
            reasoning_wh += sustainability.wh_per_query(inp + out, is_reasoning=True)
        else:
            normal_cost += row_opt_cost
            normal_wh += sustainability.wh_per_query(inp + out, is_reasoning=False)

    # Extension 3: estimate repeat reads from the observed cached-prefix ratio.
    # If a prefix is read often enough, retain cached_input_tokens; otherwise
    # rerun the optimized bill without cache savings.
    avg_cache_reads = total_input_tokens / cache_input_tokens if cache_input_tokens else 0.0
    cache_worth_it = pricing.cache_is_worth_it(avg_cache_reads, write_cost_per_m=1.0)
    if not cache_worth_it:
        opt_cost = 0.0
        for r in rows:
            inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
            pin, pout = MODEL_PRICES[r["route_tier"]]
            opt_cost += pricing.request_cost(inp, out, pin, pout, batch=bool(int(num(r["is_batch"]))))

    # Extension 4: cap reasoning traffic at 10%, retaining the most expensive
    # reasoning requests and routing the remainder through the small tier.
    reasoning_rows = [x for x in row_costs if x[1]]
    keep_count = max(1, int(len(rows) * 0.10)) if reasoning_rows else 0
    kept = set(id(x) for x in sorted(reasoning_rows, key=lambda x: x[0], reverse=True)[:keep_count])
    capped_cost = 0.0
    capped_wh = 0.0
    for item in row_costs:
        row_cost, is_reasoning, tokens, r = item
        if is_reasoning and id(item) not in kept:
            inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
            capped_cost += pricing.request_cost(inp, out, *MODEL_PRICES["small"], batch=bool(int(num(r["is_batch"]))))
            capped_wh += sustainability.wh_per_query(tokens, is_reasoning=False)
        else:
            capped_cost += row_cost
            capped_wh += sustainability.wh_per_query(tokens, is_reasoning=is_reasoning)

    reasoning_count = len(reasoning_rows)
    reasoning_pct = reasoning_count / len(rows) * 100 if rows else 0.0
    reasoning_cost_pct = reasoning_cost / opt_cost * 100 if opt_cost else 0.0
    capped_savings = (1.0 - capped_cost / opt_cost) * 100 if opt_cost else 0.0

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0

    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={len(rows)}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")
        print(f"cache extension: avg reads={avg_cache_reads:.2f}, worth it={cache_worth_it}")
        print(f"reasoning extension: {reasoning_count}/{len(rows)} requests ({reasoning_pct:.1f}%), ${reasoning_cost:,.2f}/day ({reasoning_cost_pct:.1f}% of optimized cost), {reasoning_wh:,.1f} Wh/day")
        print(f"reasoning cap 10%: ${capped_cost:,.2f}/day, {capped_wh:,.1f} Wh/day, estimated savings={capped_savings:.1f}%")

    return {
        "baseline_daily": round(base_cost, 2), "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3), "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1), "total_tokens": total_tokens,
        "request_count": len(rows), "cache_avg_reads": round(avg_cache_reads, 2), "cache_worth_it": cache_worth_it,
        "reasoning_count": reasoning_count, "reasoning_pct": round(reasoning_pct, 1),
        "reasoning_cost": round(reasoning_cost, 2), "normal_cost": round(normal_cost, 2),
        "reasoning_cost_pct": round(reasoning_cost_pct, 1), "reasoning_wh": round(reasoning_wh, 2),
        "normal_wh": round(normal_wh, 2), "reasoning_cap_cost": round(capped_cost, 2),
        "reasoning_cap_wh": round(capped_wh, 2), "reasoning_cap_savings_pct": round(capped_savings, 1),
    }


if __name__ == "__main__":
    run()
