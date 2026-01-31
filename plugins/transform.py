import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder


def clean_and_transform(df):
    if df.empty: return df, pd.DataFrame()

    # Clean Columns
    df.columns = [c.strip().replace(' ', '_').replace('-', '_').lower() for c in df.columns]

    # Fill Null (Logic quan trọng để fix NaN)
    num_cols = df.select_dtypes(include=['number']).columns
    df[num_cols] = df[num_cols].fillna(0)

    obj_cols = df.select_dtypes(include=['object']).columns
    df[obj_cols] = df[obj_cols].fillna("Unknown")

    # Hash ID
    df['customer_hash'] = df.apply(lambda x: hash(str(x.get('Debt-to-Income Ratio')) + str(x.get('gender')) + str(x.get('income'))),
                                   axis=1)
    df.drop_duplicates(subset=['customer_hash'], keep='last', inplace=True)

    # ML Data Prep
    df_ml = df.copy()
    le = LabelEncoder()
    for col in df_ml.select_dtypes(include=['object']).columns:
        df_ml[col] = df_ml[col].astype(str)
        df_ml[col] = le.fit_transform(df_ml[col])

    scaler = StandardScaler()
    exclude = ['customer_hash', 'credit_score']
    cols_scale = [c for c in df_ml.select_dtypes(include=['number']).columns if c not in exclude]
    if cols_scale:
        df_ml[cols_scale] = scaler.fit_transform(df_ml[cols_scale])

    return df, df_ml