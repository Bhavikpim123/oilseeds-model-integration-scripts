from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import numpy as np
import pandas as pd
import joblib

app = FastAPI(title="Agri Intelligence API")

MODELS: Dict[str, Any] = {}


# Request schema (NEW, CLEAN)

class CompareRequest(BaseModel):
    # Crops to compare
    crop_1: str
    crop_2: str

    # Profile / location / season
    year: int
    area_ha: float

    state: str
    district: str
    taluka: str
    season: str

    # Soil & nutrients
    soil_type: str
    N: float
    P: float
    K: float
    ph: float

    # Weather / sensor data
    temperature: float
    humidity: float
    rainfall: float
    moisture: float


# Helpers


def safe_ordinal_transform(enc, cat_cols, df: pd.DataFrame) -> np.ndarray:
    """
    Safely transform categoricals using a fitted OrdinalEncoder.
    Any unknown category (not seen during training) is mapped
    to the first known category for that column.
    """
    df = df.copy()
    for i, col in enumerate(cat_cols):
        known = list(enc.categories_[i])
        known_set = set(known)
        default_val = known[0]  # fallback if unseen

        def _fix(val):
            return val if val in known_set else default_val

        df[col] = df[col].astype(str).map(_fix)

    return enc.transform(df[cat_cols])


def build_yield_time_series(base_year: int, base_yield: float) -> Dict[str, Any]:
    """Create prev 3 + current + next 1 year yield (synthetic) for plotting."""
    prev_years = []
    growth_back = 0.03  # assume 3% growth over time
    for i in range(3, 0, -1):
        year = base_year - i
        val = base_yield / ((1 + growth_back) ** i)
        prev_years.append({"year": year, "yield_kg_ha": round(val, 2)})

    next_year = base_year + 1
    next_yield = base_yield * (1 + growth_back)

    return {
        "base_year": base_year,
        "previous_3_years": prev_years,
        "current_year_predicted": {
            "year": base_year,
            "yield_kg_ha": round(base_yield, 2),
            "confidence_low_kg_ha": round(base_yield * 0.9, 2),
            "confidence_high_kg_ha": round(base_yield * 1.1, 2),
        },
        "forecast_next_year": {
            "year": next_year,
            "yield_kg_ha": round(next_yield, 2),
        },
    }


def build_price_time_series(base_year: int, base_price: float) -> Dict[str, Any]:
    """Year-wise prev3 + current + next1 price series (synthetic trend)."""
    prev_years = []
    growth = 0.025  # 2.5% per year
    for i in range(3, 0, -1):
        year = base_year - i
        val = base_price / ((1 + growth) ** i)
        prev_years.append({"year": year, "price_rs_qt": round(val, 2)})

    next_year = base_year + 1
    next_price = base_price * (1 + growth)

    last_year_price = prev_years[-1]["price_rs_qt"]
    change_pct = (base_price - last_year_price) / last_year_price * 100

    return {
        "base_year": base_year,
        "previous_3_years": prev_years,
        "current_year_price_rs_qt": round(base_price, 2),
        "forecast_next_year": {
            "year": next_year,
            "price_rs_qt": round(next_price, 2),
        },
        "change_vs_last_year_pct": round(change_pct, 2),
        "growth_rate_pct": round(growth * 100, 2),
    }



# Model loading


@app.on_event("startup")
def load_models():
    global MODELS

    MODELS["yield"] = joblib.load("models/yield_model.pkl")
    MODELS["price"] = joblib.load("models/price_model.pkl")
    MODELS["risk"] = joblib.load("models/risk_model.pkl")
    MODELS["crop_reco"] = joblib.load("models/crop_reco_model.pkl")
    MODELS["soil"] = joblib.load("models/soil_suit_model.pkl")
    MODELS["profit"] = joblib.load("models/profit_model.pkl")
    MODELS["production"] = joblib.load("models/production_model.pkl")

    print("All models loaded.")


# Per-model prediction functions


def predict_production(req: CompareRequest, crop_name: str) -> float:
    """
    Use production_model.pkl to estimate production for this crop & year.
    Supports two save formats:
    1) { "model", "encoder", "cat_cols", "num_cols" }
    2) { "model", "feature_columns" }  (get_dummies one-hot style)
    """
    saved = MODELS["production"]
    model = saved["model"]

    # Case 1: encoder-based
    if "encoder" in saved and "cat_cols" in saved and "num_cols" in saved:
        enc = saved["encoder"]
        cat_cols = saved["cat_cols"]      # ["State_Name", "Season", "Crop"]
        num_cols = saved["num_cols"]      # ["Crop_Year", "Area"]

        cat_df = pd.DataFrame([{
            "State_Name": req.state,
            "Season": req.season,
            "Crop": crop_name,
        }])

        num_df = pd.DataFrame([{
            "Crop_Year": req.year,
            "Area": req.area_ha,
        }])

        X_cat = safe_ordinal_transform(enc, cat_cols, cat_df)
        X_num = num_df[num_cols].values
        X = np.concatenate([X_cat, X_num], axis=1)

        prod = float(model.predict(X)[0])
        return prod

    # Case 2: feature_columns with get_dummies
    elif "feature_columns" in saved:
        feature_cols = saved["feature_columns"]

        raw_df = pd.DataFrame([{
            "State_Name": req.state,
            "District_Name": req.district,
            "Crop_Year": req.year,
            "Season": req.season,
            "Crop": crop_name,
            "Area": req.area_ha,
        }])

        X = pd.get_dummies(raw_df, drop_first=True)
        X = X.reindex(columns=feature_cols, fill_value=0)

        prod = float(model.predict(X)[0])
        return prod

    else:
        raise RuntimeError(
            "production_model.pkl has unsupported structure. "
            "Expected either encoder+cat_cols+num_cols or feature_columns."
        )


def predict_yield(req: CompareRequest, crop_name: str, production_lakh_tonnes: float) -> float:
    """
    Use yield_model.pkl (trained on yieldmodel.csv).
    We assume it was trained with get_dummies and feature_columns.
    """
    saved = MODELS["yield"]
    model = saved["model"]
    feature_cols = saved["feature_columns"]

    # Your yield model used area/production in lakh units
    area_lakh_ha = req.area_ha / 100000.0

    df_raw = pd.DataFrame([{
        "cropyear_num": req.year,
        "Area (Lakh Ha)": area_lakh_ha,
        "Production (Lakh Tonnes)": production_lakh_tonnes,
        "cropname": crop_name,
        "seasonname": req.season,
        "statename": req.state,
    }])

    X = pd.get_dummies(df_raw, drop_first=True)
    X = X.reindex(columns=feature_cols, fill_value=0)

    y_pred = float(model.predict(X)[0])
    return y_pred  # kg/ha


def predict_price(req: CompareRequest, crop_name: str) -> float:
    """Predict current year's modal price using price_model.pkl."""
    saved = MODELS["price"]
    model = saved["model"]

    # INTERNAL DEFAULTS to keep behavior similar to old inputs
    market_name = req.district          # fallback: district == market
    variety = "Medium"
    grade = "FAQ"

    # Case 1: encoder-based (OrdinalEncoder)
    if "encoder" in saved and "cat_cols" in saved and "num_cols" in saved:
        enc = saved["encoder"]
        cat_cols = saved["cat_cols"]      # e.g. ["State", "District Name", ...]
        num_cols = saved["num_cols"]      # e.g. ["year", "month"]

        cat_df = pd.DataFrame([{
            "State": req.state,
            "District Name": req.district,
            "Market Name": market_name,
            "Commodity": crop_name,
            "Variety": variety,
            "Grade": grade,
        }])

        num_df = pd.DataFrame([{
            "year": req.year,
            "month": 1,    # can be made dynamic later
        }])

        X_cat = safe_ordinal_transform(enc, cat_cols, cat_df)
        X_num = num_df[num_cols].values
        X = np.concatenate([X_cat, X_num], axis=1)

        price = float(model.predict(X)[0])
        return price  # Rs./Quintal

    # Case 2: feature_columns with get_dummies
    elif "feature_columns" in saved:
        feature_cols = saved["feature_columns"]

        raw_df = pd.DataFrame([{
            "State": req.state,
            "District Name": req.district,
            "Market Name": market_name,
            "Commodity": crop_name,
            "Variety": variety,
            "Grade": grade,
            "year": req.year,
            "month": 1,
        }])

        X = pd.get_dummies(raw_df, drop_first=True)
        X = X.reindex(columns=feature_cols, fill_value=0)

        price = float(model.predict(X)[0])
        return price

    else:
        raise RuntimeError(
            "price_model.pkl has unsupported structure. "
            "Expected either encoder+cat_cols+num_cols or feature_columns."
        )


def predict_risk(req: CompareRequest, crop_name: str, yield_kg_ha: float, production: float) -> Dict[str, Any]:
    """Use risk_model.pkl to produce a numeric risk score (volatility)."""
    saved = MODELS["risk"]
    model = saved["model"]

    # Case 1: encoder-based
    if "encoder" in saved and "cat_cols" in saved and "num_cols" in saved:
        enc = saved["encoder"]
        cat_cols = saved["cat_cols"]      # ["State","Crop","Season"]
        num_cols = saved["num_cols"]      # as per training

        cat_df = pd.DataFrame([{
            "State": req.state,
            "Crop": crop_name,
            "Season": req.season,
        }])

        num_df = pd.DataFrame([{
            "Year": req.year,
            "Area": req.area_ha,
            "Production": production,
            "Yield": yield_kg_ha,
            "annual_rainfall_mm": req.rainfall,
            "rainfall_std_mm": 0.0,
            "temp_extreme_c": req.temperature + 5.0,
            "irrigation_score": 0.7,
            "loan_exposure": 0.0,
            "yield_volatility": 0.1,
            "crop_resilience": 0.5,
        }])

        X_cat = safe_ordinal_transform(enc, cat_cols, cat_df)
        X_num = num_df[num_cols].values
        X = np.concatenate([X_cat, X_num], axis=1)

        vol = float(model.predict(X)[0])

    # Case 2: feature_columns + get_dummies
    elif "feature_columns" in saved:
        feature_cols = saved["feature_columns"]

        df_raw = pd.DataFrame([{
            "State": req.state,
            "Year": req.year,
            "Crop": crop_name,
            "Season": req.season,
            "Area": req.area_ha,
            "Production": production,
            "Yield": yield_kg_ha,
            "annual_rainfall_mm": req.rainfall,
            "rainfall_std_mm": 0.0,
            "temp_extreme_c": req.temperature + 5.0,
            "irrigation_score": 0.7,
            "loan_exposure": 0.0,
            "yield_volatility": 0.1,
            "crop_resilience": 0.5,
        }])

        X = pd.get_dummies(df_raw, drop_first=True)
        X = X.reindex(columns=feature_cols, fill_value=0)
        vol = float(model.predict(X)[0])

    else:
        raise RuntimeError("risk_model.pkl structure not supported")

    # Map to band
    if vol < 0.3:
        band = "Low"
    elif vol < 0.7:
        band = "Medium"
    else:
        band = "High"

    return {
        "risk_score": vol,
        "risk_band": band,
    }


def predict_crop_reco(req: CompareRequest, crop_name: str) -> Dict[str, Any]:
    """Use crop_reco_model.pkl, and read probability of this crop."""
    saved = MODELS["crop_reco"]
    model = saved["model"]
    feature_cols = saved["feature_columns"]
    classes = saved["classes"]

    X_df = pd.DataFrame([{
        "N": req.N,
        "P": req.P,
        "K": req.K,
        "temperature": req.temperature,
        "humidity": req.humidity,
        "ph": req.ph,
        "rainfall": req.rainfall,
    }])

    X = X_df[feature_cols]
    probs = model.predict_proba(X)[0]

    class_to_prob = {c: float(p) for c, p in zip(classes, probs)}
    score_for_this_crop = class_to_prob.get(crop_name, 0.0)

    best_idx = np.argmax(probs)
    best_crop = classes[best_idx]
    best_score = float(probs[best_idx])

    return {
        "reco_score_0_1": round(score_for_this_crop, 3),
        "best_crop": best_crop,
        "best_crop_score": round(best_score, 3),
    }


def predict_soil_suitability(req: CompareRequest, crop_name: str) -> Dict[str, Any]:
    """
    Use soil_suit_model.pkl and read probability for this crop as suitability.

    Supports two save formats:
    1) { "model", "encoder", "cat_cols", "num_cols", "classes" }
    2) { "model", "feature_columns", "classes" } (trained with get_dummies)
    """
    saved = MODELS["soil"]

    if isinstance(saved, dict):
        model = saved["model"]
    else:
        model = saved
        saved = {}

    # INTERNAL default fertilizer (since app no longer sends it)
    fertilizer_name = "Urea"

    # Case 1: encoder-based
    if "encoder" in saved and "cat_cols" in saved and "num_cols" in saved:
        enc = saved["encoder"]
        cat_cols = saved["cat_cols"]
        num_cols = saved["num_cols"]
        classes = saved.get("classes", list(model.classes_))

        cat_df = pd.DataFrame([{
            "Soil Type": req.soil_type,
        }])
        num_df = pd.DataFrame([{
            "Temparature": req.temperature,
            "Humidity": req.humidity,
            "Moisture": req.moisture,
            "Nitrogen": req.N,
            "Potassium": req.K,
            "Phosphorous": req.P,
        }])

        X_cat = safe_ordinal_transform(enc, cat_cols, cat_df)
        X_num = num_df[num_cols].values
        X = np.concatenate([X_cat, X_num], axis=1)

        probs = model.predict_proba(X)[0]
        class_to_prob = {c: float(p) for c, p in zip(classes, probs)}

    # Case 2: feature_columns + get_dummies
    elif "feature_columns" in saved:
        feature_cols = saved["feature_columns"]
        classes = saved.get("classes", list(model.classes_))

        raw_df = pd.DataFrame([{
            "Temparature": req.temperature,
            "Humidity": req.humidity,
            "Moisture": req.moisture,
            "Soil Type": req.soil_type,
            "Nitrogen": req.N,
            "Potassium": req.K,
            "Phosphorous": req.P,
            "Fertilizer Name": fertilizer_name,
        }])

        X = pd.get_dummies(raw_df, drop_first=True)
        X = X.reindex(columns=feature_cols, fill_value=0)

        probs = model.predict_proba(X)[0]
        class_to_prob = {c: float(p) for c, p in zip(classes, probs)}

    # Case 3: bare model on numeric-only
    else:
        classes = list(model.classes_)
        X = pd.DataFrame([{
            "Temparature": req.temperature,
            "Humidity": req.humidity,
            "Moisture": req.moisture,
            "Nitrogen": req.N,
            "Potassium": req.K,
            "Phosphorous": req.P,
        }])
        probs = model.predict_proba(X.values)[0]
        class_to_prob = {c: float(p) for c, p in zip(classes, probs)}

    suitability = class_to_prob.get(crop_name, 0.0)
    values_list = list(class_to_prob.values())
    best_idx = int(np.argmax(values_list))
    classes_list = list(class_to_prob.keys())
    best_crop = classes_list[best_idx]
    best_score = float(values_list[best_idx])

    return {
        "suitability_score_0_1": round(suitability, 3),
        "recommended_crop": best_crop,
        "recommended_crop_score": round(best_score, 3),
    }


def predict_profit(req: CompareRequest, crop_name: str, yield_kg_ha: float, price_rs_qt: float) -> Dict[str, Any]:
    """
    Use profit_model.pkl to predict ROI% for Base scenario.

    Supports:
    1) { "model", "encoder", "cat_cols", "num_cols", ... }
    2) { "model", "feature_columns", ... } (get_dummies style)
    3) bare model on numeric-only features (fallback)
    """
    saved = MODELS["profit"]

    if isinstance(saved, dict):
        model = saved["model"]
    else:
        model = saved
        saved = {}

    # INTERNAL defaults – aligned with earlier example you used:
    # total_cost_rs_ha = 35000, investment_rs_ha = 25000
    total_cost = 35000.0
    investment = 25000.0

    # Case 1: encoder-based
    if "encoder" in saved and "cat_cols" in saved and "num_cols" in saved:
        enc = saved["encoder"]
        cat_cols = saved["cat_cols"]      # ["crop_name","scenario"]
        num_cols = saved["num_cols"]      # numeric features

        cat_df = pd.DataFrame([{
            "crop_name": crop_name,
            "scenario": "Base",
        }])

        num_df = pd.DataFrame([{
            "year": req.year,
            "expected_yield_kg_ha": yield_kg_ha,
            "selling_price_rs_qt": price_rs_qt,
            "total_cost_rs_ha": total_cost,
            "investment_rs_ha": investment,
            "rainfall_mm": req.rainfall,
            "temp_c": req.temperature,
            "price_volatility_pct": 5.0,
            "yield_variance_pct": 8.0,
        }])

        X_cat = safe_ordinal_transform(enc, cat_cols, cat_df)
        X_num = num_df[num_cols].values
        X = np.concatenate([X_cat, X_num], axis=1)
        roi = float(model.predict(X)[0])

    # Case 2: feature_columns + get_dummies
    elif "feature_columns" in saved:
        feature_cols = saved["feature_columns"]

        raw_df = pd.DataFrame([{
            "year": req.year,
            "crop_name": crop_name,
            "scenario": "Base",
            "expected_yield_kg_ha": yield_kg_ha,
            "selling_price_rs_qt": price_rs_qt,
            "total_cost_rs_ha": total_cost,
            "investment_rs_ha": investment,
            "rainfall_mm": req.rainfall,
            "temp_c": req.temperature,
            "price_volatility_pct": 5.0,
            "yield_variance_pct": 8.0,
        }])

        X = pd.get_dummies(raw_df, drop_first=True)
        X = X.reindex(columns=feature_cols, fill_value=0)
        roi = float(model.predict(X)[0])

    # Case 3: bare model numeric-only (last fallback)
    else:
        X = pd.DataFrame([{
            "year": req.year,
            "expected_yield_kg_ha": yield_kg_ha,
            "selling_price_rs_qt": price_rs_qt,
            "total_cost_rs_ha": total_cost,
            "investment_rs_ha": investment,
            "rainfall_mm": req.rainfall,
            "temp_c": req.temperature,
            "price_volatility_pct": 5.0,
            "yield_variance_pct": 8.0,
        }])
        roi = float(model.predict(X.values)[0])

    return {
        "roi_pct": roi,
        "total_cost_rs_ha": total_cost,
        "investment_rs_ha": investment,
    }



# Run all models for one crop

def run_all_models_for_crop(req: CompareRequest, crop_name: str) -> Dict[str, Any]:
    # 1. Production
    production = predict_production(req, crop_name)

    # 2. Yield
    production_lakh_tonnes = production / 100000.0  # adjust if your units differ
    yield_kg_ha = predict_yield(req, crop_name, production_lakh_tonnes)
    yield_ts = build_yield_time_series(req.year, yield_kg_ha)

    # 3. Price
    price_rs_qt = predict_price(req, crop_name)
    price_ts = build_price_time_series(req.year, price_rs_qt)

    # 4. Risk
    risk_res = predict_risk(req, crop_name, yield_kg_ha, production)

    # 5. Crop recommendation
    crop_reco_res = predict_crop_reco(req, crop_name)

    # 6. Soil suitability
    soil_res = predict_soil_suitability(req, crop_name)

    # 7. Profit / ROI
    profit_res = predict_profit(req, crop_name, yield_kg_ha, price_rs_qt)

    return {
        "crop_name": crop_name,
        "yield_model": yield_ts,
        "price_model": price_ts,
        "production_model": {
            "predicted_production": production
        },
        "risk_model": risk_res,
        "crop_recommendation_model": crop_reco_res,
        "soil_suitability_model": soil_res,
        "profit_model": profit_res,
    }



# Routes

@app.get("/")
def root():
    return {"status": "ok", "message": "Agri Intel API is running"}


@app.post("/compare")
def compare_crops(req: CompareRequest) -> Dict[str, Any]:
    crop1_res = run_all_models_for_crop(req, req.crop_1)
    crop2_res = run_all_models_for_crop(req, req.crop_2)

    return {
        "input": req.dict(),
        "crops": [crop1_res, crop2_res],
    }
