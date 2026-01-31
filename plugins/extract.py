import pandas as pd
import os

STATE_FILE = '/opt/airflow/data/state.txt'


def extract_batch(file_path, batch_size=100):
    if not os.path.exists(STATE_FILE):
        offset = 0
    else:
        with open(STATE_FILE, 'r') as f:
            try:
                offset = int(f.read().strip())
            except:
                offset = 0

    print(f"Reading from line {offset}...")
    try:
        header = pd.read_csv(file_path, nrows=0).columns
        df = pd.read_csv(file_path, skiprows=range(1, offset + 1), nrows=batch_size, header=None)
        if df.empty: return pd.DataFrame()
        df.columns = header
    except Exception as e:
        print(e)
        return pd.DataFrame()

    with open(STATE_FILE, 'w') as f:
        f.write(str(offset + len(df)))
    return df