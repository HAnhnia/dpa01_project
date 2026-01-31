from sklearn.ensemble import RandomForestRegressor
import pandas as pd


def train_and_predict_risk(df_ml, df_original):
    if df_ml.empty: return pd.DataFrame()

    target = 'credit_score'
    features = [c for c in df_ml.columns if c not in ['customer_hash', target]]

    X = df_ml[features]
    y = df_ml[target]

    rf = RandomForestRegressor(n_estimators=50, random_state=42)
    rf.fit(X, y)
    predictions = rf.predict(X)

    df_res = df_original.copy()
    df_res['predicted_credit_score'] = predictions
    # Giả sử < 650 là rủi ro cao
    df_res['is_high_risk'] = df_res['predicted_credit_score'] < 650

    return df_res[df_res['is_high_risk'] == True]