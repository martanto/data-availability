from pathlib import Path

import pandas as pd


def load_data(filepath: str | Path) -> pd.DataFrame:
    path = Path(filepath)
    if path.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    df = df[["date", "completeness"]].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["completeness"] = df["completeness"].clip(0, 100)

    return df.sort_values("date").reset_index(drop=True)
