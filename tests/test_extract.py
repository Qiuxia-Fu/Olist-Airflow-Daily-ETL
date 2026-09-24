from datetime import date

import pandas as pd
import pytest

from extract.extract_incremental import validate, ValidationError, list_pending_dates
import extract.extract_incremental as extract_mod


def make_df(**overrides):
    base = {
        "order_id": ["a1", "a2", "a3"],
        "customer_id": ["c1", "c2", "c3"],
        "order_status": ["delivered", "delivered", "shipped"],
        "order_purchase_timestamp": ["2018-05-01", "2018-05-02", "2018-05-03"],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def test_validate_passes_on_clean_data():
    validate(make_df())  # 不抛异常就是通过


def test_validate_raises_on_duplicate_order_id():
    df = make_df(order_id=["a1", "a1", "a3"])
    with pytest.raises(ValidationError, match="duplicated order_id"):
        validate(df)


def test_validate_raises_on_null_order_id():
    df = make_df(order_id=["a1", None, "a3"])
    with pytest.raises(ValidationError, match="empty"):
        validate(df)


def test_validate_raises_on_missing_column():
    df = make_df().drop(columns=["customer_id"])
    with pytest.raises(ValidationError, match="Missing required"):
        validate(df)


def test_validate_raises_on_empty_dataframe():
    df = make_df().iloc[0:0]
    with pytest.raises(ValidationError, match="Empty data"):
        validate(df)


def test_list_pending_dates_returns_only_dates_after_watermark(tmp_path, monkeypatch):
    fake_raw = tmp_path / "raw_source"
    fake_raw.mkdir()
    for d in ["2018-05-24", "2018-05-25", "2018-05-26", "2018-05-27"]:
        (fake_raw / f"{d}.csv").write_text("order_id\n")

    monkeypatch.setattr(extract_mod, "RAW_SOURCE_DIR", fake_raw)

    pending = list_pending_dates(date(2018, 5, 25))
    assert pending == [date(2018, 5, 26), date(2018, 5, 27)]


def test_list_pending_dates_returns_all_when_watermark_is_none(tmp_path, monkeypatch):
    fake_raw = tmp_path / "raw_source"
    fake_raw.mkdir()
    for d in ["2018-05-24", "2018-05-25"]:
        (fake_raw / f"{d}.csv").write_text("order_id\n")

    monkeypatch.setattr(extract_mod, "RAW_SOURCE_DIR", fake_raw)

    pending = list_pending_dates(None)
    assert len(pending) == 2
