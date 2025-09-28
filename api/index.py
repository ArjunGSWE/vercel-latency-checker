import json
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List

# --- Data Loading ---

df = pd.read_json(../q-vercel-latency.json)

# -------------------------


# --- Pydantic Models ---
class LatencyRequest(BaseModel):
    """Defines the expected input JSON body."""

    regions: List[str] = Field(..., example=["emea", "apac"])
    threshold_ms: int = Field(..., example=180)


class RegionMetric(BaseModel):
    """Defines the expected per-region output structure."""

    region: str
    avg_latency: float
    p95_latency: float
    avg_uptime: float
    breaches: int


# --- FastAPI App ---
app = FastAPI(title="eShopCo Latency Checker")

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.post("/metrics", response_model=List[RegionMetric])
def get_latency_metrics(request_data: LatencyRequest):
    """
    Calculates per-region latency and uptime metrics based on a threshold.
    """
    # 1. Filter the data by requested regions
    filtered_df = df[df["region"].isin(request_data.regions)].copy()

    if filtered_df.empty:
        return []

    results = []

    # 2. Calculate metrics for each requested region
    for region in request_data.regions:
        region_data = filtered_df[filtered_df["region"] == region]

        if region_data.empty:
            continue

        # Metrics Calculation
        avg_lat = region_data["latency_ms"].mean()
        p95_lat = region_data["latency_ms"].quantile(0.95)
        avg_up = region_data["uptime_pct"].mean()

        # Breaches calculation (count of records above threshold)
        breaches_count = (region_data["latency_ms"] > request_data.threshold_ms).sum()

        results.append(
            {
                "region": region,
                "avg_latency": round(avg_lat, 2),
                "p95_latency": round(p95_lat, 2),
                "avg_uptime": round(avg_up, 2),
                "breaches": int(breaches_count),
            }
        )

    return results
