# SmartFreight

**Predictive Supply Chain and Delay Risk Engine**

SmartFreight estimates the risk of late delivery for a shipment before dispatch. It combines a machine-learning prediction with an arrival-date weather adjustment and presents the result in an operational dashboard, helping logistics teams identify shipments that may need attention before an SLA is breached.

## Team ThreeLoops

- Rishav Dev
- Vaibhavi Srivastava
- Saksham Singhania

## Project Overview

The system has three main parts:

1. An **XGBoost classifier** trained on historical order data to estimate late-delivery risk.
2. A **FastAPI REST API** that validates inputs and serves predictions through `POST /predict`.
3. A **Streamlit dashboard** for entering shipment details and viewing risk results and route telemetry.

### Highlights

- Separates the prediction API from the dashboard, with Pydantic request and response validation.
- Looks up forecast weather for the expected arrival date at the destination using Open-Meteo.
- Reports a weather delay adjustment separately from the model's base operational risk.
- Geocodes destination cities with Geopy, calculates geodesic distance from the Delhi hub, and maps destinations to market regions.
- Rejects physically implausible inputs, such as zero-day intercity transit.
- Includes a risk assessment calculator and a 3D route telemetry map, with stable, caution, and critical status labels.

## How It Works

1. An operator enters shipment details and a destination in the dashboard.
2. The client geocodes the destination, calculates distance from the Delhi hub, and retrieves forecast weather for the expected arrival date.
3. The dashboard sends shipment features to the FastAPI `POST /predict` endpoint.
4. The API validates the request, applies the saved feature encoding schema, and gets a late-delivery probability from the XGBoost model.
5. The response includes the base prediction and weather adjustment; the dashboard displays the risk, attribution, and route status.

## Data and Model

The model is described as using the public **DataCo Smart Supply Chain Dataset**, an order-level dataset covering approximately 2015–2018 and mostly US regions. The target is `Late_delivery_risk` (`1` for late, `0` for on time).

Features described in the report include payment type, shipping mode, scheduled shipping days, sales per customer, item quantity, product price, discount, benefit per order, customer segment, department, and order region. Fields that reveal the outcome after dispatch—such as actual shipping days and delivery status—should be excluded to avoid target leakage.

The dataset does not contain weather observations and does not represent the deployed Delhi-to-India routes. Weather is therefore a rule-based adjustment layered on the model output; it is not a factor learned by the classifier. Geodesic distance is a straight-line lower bound rather than road distance. The report also notes that training values are in USD while the dashboard displays INR, and that these values are not converted in the model.

## Technology

- Python 3.9+
- XGBoost
- pandas, NumPy, scikit-learn
- FastAPI and Pydantic
- Streamlit
- Geopy and OpenStreetMap Nominatim
- Open-Meteo API
- Pickle model and feature pipeline artifacts

## Repository Layout

The project report describes the following files and directories:

```text
.
├── data/
│   └── DataCoSupplyChainDataset.csv
├── models/
│   ├── final_xgb_model.pkl
│   └── processed_data_pipeline.pkl
├── FastAPI.py
├── app.py
├── EDA.py
├── feature_data.py
├── model_training.py
├── requirements.txt
└── README.md
```

## Run Locally

The report gives these commands for running the API and dashboard:

```bash
pip install -r requirements.txt
uvicorn FastAPI:app --reload
```

In a second terminal:

```bash
streamlit run app.py
```

The API is served by Uvicorn, and the Streamlit app calls its `POST /predict` endpoint. Confirm that the files and dependencies listed above are present in your checkout and that the dashboard is configured to use the API address before running.

## API

The API exposes `POST /predict`. It accepts a JSON request validated by Pydantic and returns a JSON prediction response. The following examples are illustrative, based on the project report; confirm the exact field names and response schema against `FastAPI.py` before integrating another client.

Illustrative request:

```json
{
  "order_quantity": 1,
  "sales_per_customer": 50,
  "product_price": 10,
  "shipping_mode": "Standard Class",
  "scheduled_shipping_days": 2,
  "destination_city": "Chennai",
  "origin_hub": "Delhi Hub (North HQ)"
}
```

Illustrative response:

```json
{
  "late_delivery_risk_prob": 0.81,
  "late_delivery_risk_pred": 1,
  "weather_delay_penalty_pct": 12.5,
  "status": "CRITICAL SLA RISK"
}
```

Invalid inputs are expected to receive FastAPI validation errors. The report cites HTTP 422 as the default behavior; verify the implementation's error handling in `FastAPI.py`.

## Evaluation

The report lists the following held-out test results:

| Metric | Reported value |
| --- | ---: |
| Accuracy | 89.4% |
| ROC-AUC | 0.91 |
| F1 score, late class | Not reported |
| Test split ratio and random state | Not reported |

ROC-AUC measures how well the model ranks late shipments above on-time shipments across thresholds. Accuracy and F1 depend on the selected classification threshold. The reported metrics should be treated as provisional until the training code confirms that post-dispatch leakage fields were excluded and the split details and missing F1 score are recorded. The report does not provide independent evaluation of the weather adjustment.

## Limitations and Next Steps

- The held-out data comes from the same historical dataset and does not establish performance on Indian routes.
- The weather adjustment is rule-based and has no reported standalone accuracy measurement.
- Geodesic distance approximates a lower bound on travel distance and does not represent road routing.
- The dataset uses USD, while the dashboard displays INR; model values are not converted.
- Useful next steps include checking probability calibration, reporting precision and recall at the dashboard threshold, evaluating on regional shipment data, and comparing logged predictions with actual delivery outcomes.

## License

The project report identifies the repository as MIT-licensed. Include the project's `LICENSE` file in the checkout to make the license terms available.
