from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert


def postgres_upsert_method(table, conn, keys, data_iter):
    data = [dict(zip(keys, row)) for row in data_iter]
    stmt = insert(table.table).values(data)
    update_cols = {c.name: c for c in stmt.excluded if c.name not in ['customer_hash']}
    on_conflict = stmt.on_conflict_do_update(index_elements=['customer_hash'], set_=update_cols)
    conn.execute(on_conflict)


def upsert_data(df, table_name, conn_str):
    if df.empty: return
    engine = create_engine(conn_str)

    with engine.begin() as conn:
        # Check bảng tồn tại chưa, chưa thì tạo (tự động dựa trên DF)
        exists = conn.execute(text(f"SELECT to_regclass('{table_name}')")).scalar()
        if not exists:
            # Load schema mẫu
            df.head(0).to_sql(table_name, conn, if_exists='replace', index=False)
            conn.execute(text(f"ALTER TABLE {table_name} ADD PRIMARY KEY (customer_hash);"))

        print(f"Loading {len(df)} rows into {table_name}...")
        df.to_sql(table_name, con=conn, if_exists='append', index=False, method=postgres_upsert_method)