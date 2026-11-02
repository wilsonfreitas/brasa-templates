import io
import json
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from brasa import process_etl
from brasa.downloaders import bcb_currency_download
from brasa.downloaders.downloaders import BCBCurrencyDownloader
from brasa.engine import (
    CacheManager,
    MarketDataTemplate,
    download_marketdata,
    process_marketdata,
    retrieve_template,
)
from brasa.engine.catalog import DatasetCatalog
from brasa.engine.exceptions import DownloadException
from brasa.fieldsets import Fieldset
from brasa.queries import get_dataset


def test_bcb_currency_downloader_serializes_dataframe_to_json():
    df = pd.DataFrame(
        [
            {
                "dataHoraCotacao": "2025-01-02 10:08:23.123",
                "cotacaoCompra": 6.1234,
                "cotacaoVenda": 6.1240,
                "paridadeCompra": 1.0,
                "paridadeVenda": 1.0,
                "tipoBoletim": "Abertura",
            }
        ]
    )

    fake_query = MagicMock()
    fake_query.parameters.return_value.collect.return_value = df
    fake_endpoint = MagicMock()
    fake_endpoint.query.return_value = fake_query
    fake_ptax = MagicMock()
    fake_ptax.get_endpoint.return_value = fake_endpoint

    with patch(
        "brasa.downloaders.downloaders.PTAX", return_value=fake_ptax
    ) as mock_ptax:
        downloader = BCBCurrencyDownloader(
            currency="USD", start=date(2025, 1, 2), end=date(2025, 1, 2)
        )
        result = downloader.download()

    mock_ptax.assert_called_once_with()
    fake_ptax.get_endpoint.assert_called_once_with("CotacaoMoedaPeriodo")
    fake_query.parameters.assert_called_once_with(
        moeda="USD", dataInicial=date(2025, 1, 2), dataFinalCotacao=date(2025, 1, 2)
    )
    assert isinstance(result, io.BytesIO)
    data = json.loads(result.read().decode("utf8"))
    assert len(data) == 1
    assert data[0]["dataHoraCotacao"] == "2025-01-02 10:08:23.123"
    assert data[0]["cotacaoVenda"] == 6.1240


def test_bcb_currency_downloader_raises_download_exception_on_error():
    with patch("brasa.downloaders.downloaders.PTAX", side_effect=Exception("boom")):
        downloader = BCBCurrencyDownloader(
            currency="USD", start=date(2025, 1, 1), end=date(2025, 1, 1)
        )
        with pytest.raises(DownloadException, match="USD"):
            downloader.download()


def test_bcb_currency_download_helper_is_exported():
    assert callable(bcb_currency_download)


def test_load_bcb_currency_template():
    tpl = MarketDataTemplate("templates/bcb/bcb-currency.yaml")

    assert tpl.has_downloader
    assert tpl.has_reader
    assert tpl.id == "bcb-currency"


def test_bcb_currency_template_fields():
    tpl = MarketDataTemplate("templates/bcb/bcb-currency.yaml")

    assert isinstance(tpl.fields, Fieldset)
    expected = {
        "refdate": "datetime",
        "currency": "string",
        "bid": "numeric",
        "ask": "numeric",
        "parity_bid": "numeric",
        "parity_ask": "numeric",
        "bulletin_type": "string",
        "downloaded_at": "datetime",
    }
    assert len(tpl.fields) == len(expected)
    for name, type_name in expected.items():
        assert tpl.fields[name].type_name == type_name, name


def test_retrieve_bcb_currency_template():
    tpl = retrieve_template("bcb-currency")
    assert tpl is not None
    assert tpl.id == "bcb-currency"


@pytest.mark.integration
def test_bcb_currency_download_and_process_usd():
    """Integration: download USD intraday PTAX quotes for a small window and process."""
    download_marketdata(
        "bcb-currency",
        currency="USD",
        start=date(2025, 1, 2),
        end=date(2025, 1, 10),
    )
    process_marketdata("bcb-currency")

    man = CacheManager()
    ds_path = Path(man.db_path("input/bcb-currency"))
    assert ds_path.exists(), f"Expected dataset at {ds_path}"


@pytest.mark.integration
def test_bcb_currency_download_multiple_currencies():
    """Integration: download multiple currencies via KwargsIterator."""
    download_marketdata(
        "bcb-currency",
        currency=["USD", "EUR"],
        start=date(2025, 1, 2),
        end=date(2025, 1, 3),
    )
    process_marketdata("bcb-currency")

    man = CacheManager()
    ds_path = Path(man.db_path("input/bcb-currency"))
    assert ds_path.exists()


def test_bcb_currency_consolidated_drops_null_refdate_bulletins():
    """Regression for WIL-125: bulletins with null refdate must not form candles.

    The PTAX API serves the next business day's pre-open Abertura bulletin
    without a timestamp; those rows must be excluded from candle grouping.
    """
    man = CacheManager()
    table = pa.table(
        {
            "refdate": pa.array(
                [
                    datetime(2026, 6, 19, 9, 0),
                    datetime(2026, 6, 19, 10, 0),
                    datetime(2026, 6, 19, 11, 0),
                    datetime(2026, 6, 19, 12, 0),
                    None,
                ],
                pa.timestamp("us"),
            ),
            "currency": ["USD"] * 5,
            "bid": pa.array([4.99, 5.19, 4.79, 5.09, 9.89], pa.float64()),
            "ask": pa.array([5.0, 5.2, 4.8, 5.1, 9.9], pa.float64()),
            "parity_bid": pa.array([1.0] * 5, pa.float64()),
            "parity_ask": pa.array([1.0] * 5, pa.float64()),
            "bulletin_type": [
                "Abertura",
                "Intermediário",
                "Intermediário",
                "Fechamento",
                "Abertura",
            ],
            "downloaded_at": pa.array(
                [datetime(2026, 6, 22, 5, 42)] * 5, pa.timestamp("us")
            ),
        }
    )
    path = man.db_path("input/bcb-currency")
    Path(path).mkdir(parents=True, exist_ok=True)
    pq.write_to_dataset(table, root_path=path, partition_cols=["currency"])
    DatasetCatalog().register_dataset(
        layer="input",
        dataset_name="bcb-currency",
        schema=table.schema,
        partitioning=["currency"],
        source_template="bcb-currency",
    )

    process_etl("bcb-currency-consolidated")

    df = (
        get_dataset(
            "bcb-currency",
            layer="staging",
            use_template_schema=False,
            use_catalog_schema=True,
        )
        .to_table()
        .to_pandas()
    )
    assert len(df) == 1
    row = df.iloc[0]
    assert pd.Timestamp(row["refdate"]).date() == date(2026, 6, 19)
    assert row["symbol"] == "BRLUSD"
    assert row["open"] == pytest.approx(1 / 5.0)
    assert row["high"] == pytest.approx(1 / 4.8)
    assert row["low"] == pytest.approx(1 / 5.2)
    assert row["close"] == pytest.approx(1 / 5.1)
