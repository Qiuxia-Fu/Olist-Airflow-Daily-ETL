import pandas as pd
from pathlib import Path

SOURCE_FILE = "data/olist_orders_dataset.csv"
OUTPUT_DIR = Path("raw_source")
WINDOW_START = "2018-04-01"
WINDOW_END = "2018-05-30"


def main():
    df = pd.read_csv(SOURCE_FILE)
    df = df.drop(columns=["Unnamed: 8"], errors="ignore")

    df["order_purchase_timestamp"] = pd.to_datetime(
        df["order_purchase_timestamp"], format="%Y/%m/%d %H:%M"
    )

    mask = (df["order_purchase_timestamp"] >= WINDOW_START) & (
        df["order_purchase_timestamp"] <= WINDOW_END + " 23:59:59"
    )
    window_df = df[mask].copy()
    window_df["order_date"] = window_df["order_purchase_timestamp"].dt.date

    OUTPUT_DIR.mkdir(exist_ok=True)

    for order_date, day_df in window_df.groupby("order_date"):
        out_path = OUTPUT_DIR / f"{order_date}.csv"
        day_df.drop(columns=["order_date"]).to_csv(out_path, index=False)
        print(f"{order_date}: {len(day_df)} 条订单 -> {out_path}")


if __name__ == "__main__":
    main()
