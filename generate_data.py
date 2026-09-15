"""
Generates dummy Careem Ads agency pipeline data for the prototype dashboard.
All company names, deal values, and contacts are fictional/illustrative -
no confidential or real Careem data is used anywhere in this file.
"""
import random
import datetime as dt
import pandas as pd

random.seed(42)

AGENCIES = [
    ("WPP", "GroupM"),
    ("Publicis Groupe", "Publicis Media"),
    ("Omnicom", "OMD"),
    ("IPG", "Mediabrands"),
    ("Dentsu", "Dentsu Media"),
    ("Havas", "Havas Media"),
]

MARKETS = ["UAE", "KSA", "Egypt"]

# Illustrative non-endemic and endemic client categories agencies might place
CLIENT_CATEGORIES = {
    "Non-endemic": ["Beauty & Personal Care", "Telco", "Banking & Fintech",
                    "Auto", "Electronics", "Fashion & Retail"],
    "Endemic": ["QSR & Food", "Grocery & Retail", "Travel & Mobility"],
}

STAGES = ["Prospecting", "Proposal Sent", "Negotiation", "JBP Signed", "Live Campaign", "Renewal"]
STAGE_WEIGHT = {"Prospecting": 0.10, "Proposal Sent": 0.30, "Negotiation": 0.55,
                "JBP Signed": 0.80, "Live Campaign": 0.95, "Renewal": 0.90}

QUARTERS = ["Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026"]

rows = []
deal_id = 1000

for holding, network in AGENCIES:
    for market in MARKETS:
        # Each agency x market has a handful of deals in different stages
        n_deals = random.randint(3, 6)
        for _ in range(n_deals):
            category_type = random.choices(["Non-endemic", "Endemic"], weights=[0.65, 0.35])[0]
            client_vertical = random.choice(CLIENT_CATEGORIES[category_type])
            stage = random.choices(STAGES, weights=[0.15, 0.20, 0.20, 0.15, 0.20, 0.10])[0]
            base_value = random.randint(80, 900) * 1000  # USD
            probability = round(min(0.98, max(0.05, STAGE_WEIGHT[stage] + random.uniform(-0.06, 0.06))), 2)
            quarter = random.choice(QUARTERS)
            # Most deals move at a normal pace; ~18% are genuinely stalled (long tail)
            if random.random() < 0.18:
                days_in_stage = random.randint(55, 140)
            else:
                days_in_stage = random.randint(2, 35)
            last_activity = dt.date(2026, 9, 15) - dt.timedelta(days=random.randint(0, min(days_in_stage, 20)))
            jbp_target = base_value * random.uniform(1.1, 1.6) if stage in ["JBP Signed", "Live Campaign", "Renewal"] else None

            rows.append({
                "deal_id": f"CA-{deal_id}",
                "holding_group": holding,
                "agency_network": network,
                "market": market,
                "client_vertical": client_vertical,
                "category_type": category_type,
                "stage": stage,
                "pipeline_value_usd": base_value,
                "win_probability": probability,
                "weighted_value_usd": round(base_value * probability),
                "quarter": quarter,
                "days_in_current_stage": days_in_stage,
                "last_activity_date": last_activity.isoformat(),
                "jbp_annual_target_usd": round(jbp_target) if jbp_target else "",
            })
            deal_id += 1

df = pd.DataFrame(rows)
df.to_csv("careem_ads_agency_pipeline_dummy.csv", index=False)
print(f"Generated {len(df)} rows -> careem_ads_agency_pipeline_dummy.csv")
print(df.head(10).to_string())
