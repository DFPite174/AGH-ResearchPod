"""
DuckDB Data Lake Client.
Connects directly to the primary local lake at C:\\Users\\SKT80\\Downloads\\data_lake\\quant_lake.duckdb.
"""

from pathlib import Path
from typing import Optional, Any
import duckdb
import pandas as pd

DEFAULT_LAKE_PATH = Path(r"C:\Users\SKT80\Downloads\data_lake\quant_lake.duckdb")


def get_lake_connection(db_path: Optional[Path] = None, read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """
    Returns an open connection to the DuckDB quant lake.
    """
    path = db_path or DEFAULT_LAKE_PATH
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path), read_only=read_only if path.exists() else False)


def query_lake(sql: str, params: Optional[list] = None, db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Executes a vectorized SQL query against the local DuckDB lake and returns a DataFrame.
    """
    con = get_lake_connection(db_path=db_path, read_only=True)
    try:
        if params:
            return con.execute(sql, params).df()
        return con.execute(sql).df()
    finally:
        con.close()
