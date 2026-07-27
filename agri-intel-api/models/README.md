# Machine Learning Models Directory

This directory is intended to store the pre-trained `.pkl` machine learning models used by the Agricultural Intelligence API. 

Due to their large file size and for security reasons, the actual `.pkl` files are **ignored by Git** and are not hosted in this repository.

## Required Models

To successfully run the API locally or in production, you must download the following models and place them directly in this folder (`agri-intel-api/models/`):

1. **`yield_model.pkl`**: Predicts crop yield (kg/ha) based on historical data.
2. **`price_model.pkl`**: Forecasts market prices (Rs./Quintal) for crops.
3. **`risk_model.pkl`**: Evaluates crop cultivation risk and volatility.
4. **`crop_reco_model.pkl`**: Recommends the optimal crop based on soil nutrients and weather.
5. **`soil_suit_model.pkl`**: Calculates the suitability of soil for specific crops.
6. **`profit_model.pkl`**: Predicts expected ROI and profitability metrics.
7. **`production_model.pkl`**: Estimates total crop production volume.

## Download Instructions

The models are hosted securely on Google Drive. 

**Download Link:** *[Insert your Google Drive link here]*

**Steps to configure:**
1. Navigate to the Google Drive link provided above.
2. Download all the `.pkl` files listed.
3. Move the downloaded files into this exact directory (`agri-intel-api/models/`).
4. Ensure the filenames match the required names listed above exactly.

Once the models are in place, you can start the API server normally.
