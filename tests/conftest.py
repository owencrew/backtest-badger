from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from backtest_badger.candles import CandleObservation


@pytest.fixture
def config_env():
    return {
        "POSTGRES_DB": "test_badger",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "private-test-password",
    }


@pytest.fixture
def candle_observation():
    D = Decimal
    OPEN = datetime(2024, 1, 1, tzinfo=UTC)
    OBSERVED = OPEN + timedelta(days=1)
    return CandleObservation(
        market_id=1,
        interval_seconds=14400,
        open_time=OPEN,
        open=D("42000.123456789012345678901234567890123456789"),
        high=D("43000"),
        low=D("41000"),
        close=D("42500.000000000000000000000000000000000000001"),
        base_volume=D("123.000000000000000000000000000000000000001"),
        quote_volume=D("5200000.123456789012345678901234567890123456789"),
        trade_count=1234,
        taker_buy_base_volume=D("60.0123456789012345678901234567890123456789"),
        taker_buy_quote_volume=D("2500000.123456789012345678901234567890123456789"),
        observed_at=OBSERVED,
        source_kind="archive",
        source_url="https://example.invalid/synthetic.zip",
        source_sha256="a" * 64,
    )


@pytest.fixture
def archive_rows():
    """Complete synthetic month; integer epoch arithmetic and long exact decimals."""

    def make(request):
        epoch = datetime(1970, 1, 1, tzinfo=UTC)
        tick = timedelta(microseconds=1 if request.month >= "2025-01" else 1000)
        rows = []
        for opened in request.grid:
            rows.append(
                [
                    str((opened - epoch) // tick),
                    "100.123456789012345678901234567890123456789",
                    "110",
                    "90",
                    "105",
                    "123.000000000000000000000000000000000000001",
                    str(
                        (opened + timedelta(seconds=request.seconds) - epoch) // tick
                        - 1
                    ),
                    "12000.123456789012345678901234567890123456789",
                    "1234",
                    "60",
                    "6000",
                    "17928899.62484339",
                ]
            )
        return rows

    return make


@pytest.fixture
def archive_download(archive_rows):
    import csv
    import hashlib
    import io
    from zipfile import ZIP_DEFLATED, ZipFile

    from backtest_badger.archives import DownloadedArchive

    def make(request, rows=None, *, member=None, body=None):
        if body is None:
            csv_text = io.StringIO()
            csv.writer(csv_text).writerows(
                archive_rows(request) if rows is None else rows
            )
            buffer = io.BytesIO()
            with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
                archive.writestr(member or request.stem + ".csv", csv_text.getvalue())
            body = buffer.getvalue()
        digest = hashlib.sha256(body).hexdigest()
        checksum = f"{digest}  {request.stem}.zip\n".encode()
        return DownloadedArchive(
            body, checksum, digest, datetime(2026, 1, 1, tzinfo=UTC)
        )

    return make
