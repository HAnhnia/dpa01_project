from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.operators.empty import EmptyOperator
import sys
import os
import pandas as pd
import json

# Import plugins
sys.path.append("/opt/airflow/plugins")
from extract import extract_batch
from transform import clean_and_transform
from load import upsert_data
from ml_model import train_and_predict_risk

STAGING_CONN = os.getenv("STAGING_CONN_STR")
PROD_CONN = os.getenv("PROD_CONN_STR")
DATA_PATH = '/opt/airflow/data/Financial_risk_assessment.csv'


@dag(
    dag_id='financial_final_prod_v6',
    default_args={'owner': 'data_engineer'},
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False
)
def financial_pipeline():
    # 1. Extract -> JSON String
    @task(task_id='1_extract')
    def task_extract():
        df = extract_batch(DATA_PATH, batch_size=100)
        if df.empty: return None
        return df.to_json(orient='records')

    # 2. Transform -> JSON String
    @task(task_id='2_transform')
    def task_transform(raw_json):
        if not raw_json: return None
        df_raw = pd.read_json(raw_json)
        df_clean, df_ml = clean_and_transform(df_raw)
        return {
            "clean": df_clean.to_json(orient='records'),
            "ml": df_ml.to_json(orient='records')
        }

    # 3. Load Staging
    @task(task_id='3_load_staging')
    def task_load_staging(data):
        if not data: return
        df_ml = pd.read_json(data['ml'])
        upsert_data(df_ml, 'staging_features_encoded', STAGING_CONN)

    # 4. Predict
    @task(task_id='4_predict')
    def task_predict(data):
        if not data: return None
        df_clean = pd.read_json(data['clean'])
        df_ml = pd.read_json(data['ml'])

        df_risk = train_and_predict_risk(df_ml, df_clean)
        if df_risk.empty: return None
        return df_risk.to_json(orient='records')

    # 5. Load Prod (Vào dvdrental máy thật)
    @task(task_id='5_load_prod')
    def task_load_prod(risk_json):
        if not risk_json:
            print("👍 Không có rủi ro cao.")
            return
        df_risk = pd.read_json(risk_json)
        # Ghi vào bảng 'prod_high_risk_customers' trong dvdrental
        upsert_data(df_risk, 'prod_high_risk_customers', PROD_CONN)
        print(f"🚀 Đã đẩy {len(df_risk)} dòng vào DB Local (dvdrental).")

    start = EmptyOperator(task_id='start')
    end = EmptyOperator(task_id='end')

    raw = task_extract()
    transformed = task_transform(raw)
    load_stage = task_load_staging(transformed)
    prediction = task_predict(transformed)
    load_prod = task_load_prod(prediction)

    start >> raw >> transformed
    transformed >> [load_stage, prediction]
    prediction >> load_prod >> end


financial_pipeline()