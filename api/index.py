from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from pathlib import Path
import os

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

DATA_FILE = os.path.join(os.getcwd(), "api", "q-vercel-latency.json")
# OR, if your function bundle's root is the 'api' directory:
# DATA_FILE = os.path.join(os.getcwd(), "q-vercel-latency.json")

# Let's try the direct reference first, as Vercel typically bundles the function's directory as the root.
try:
    # Try the simplest form first, relying on the function's root being the 'api' directory
    DATA_FILE = Path("q-vercel-latency.json")
    df = pd.read_json(DATA_FILE)
except Exception as e:
    # If that fails, try the os.getcwd() method, assuming the file is *in* the API directory
    # If your project structure is /api/index.py and /api/q-vercel-latency.json
    data_path = os.path.join(os.getcwd(), "api", "q-vercel-latency.json")
    if not os.path.exists(data_path):
        # Fallback to the structure where the API dir is the root
        data_path = os.path.join(os.getcwd(), "q-vercel-latency.json")

    # You might want to print the path to Vercel logs to debug:
    print(f"Attempting to load data from: {data_path}")
    df = pd.read_json(data_path)


@app.get("/")
async def root():
    return {"message": "Vercel Latency Analytics API is running."}


@app.post("/api/")
async def get_latency_stats(request: Request):
    payload = await request.json()
    regions_to_process = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 200)

    results = []

    for region in regions_to_process:
        region_df = df[df["region"] == region]

        if not region_df.empty:
            avg_latency = round(region_df["latency_ms"].mean(), 2)
            p95_latency = round(np.percentile(region_df["latency_ms"], 95), 2)
            avg_uptime = round(region_df["uptime_pct"].mean(), 3)
            breaches = int(region_df[region_df["latency_ms"] > threshold].shape[0])

            results.append(
                {
                    "region": region,
                    "avg_latency": avg_latency,
                    "p95_latency": p95_latency,
                    "avg_uptime": avg_uptime,
                    "breaches": breaches,
                }
            )

    return {"regions": results}
