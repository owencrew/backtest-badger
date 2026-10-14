"""Health checks and explicitly bounded archive ingestion."""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import psycopg

from backtest_badger.archives import ArchiveRequest
from backtest_badger.config import load_settings
from backtest_badger.db import check_database, connect_database
from backtest_badger.features import prepare_dataset
from backtest_badger.history import backfill_history, history_requests
from backtest_badger.ingestion import ingest_archive
from backtest_badger.recent import sync_recent
from backtest_badger.research import coverage_report, export_dataset, selections
from backtest_badger.revalidation import apply_revalidation, review_history

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="badger", description="A little badger. A lot of backtests."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("health", help="Validate application configuration")
    commands.add_parser("db-health", help="Check PostgreSQL connectivity")
    forward = commands.add_parser(
        "record-forward",
        help="Record four unscored forecasts for the current 4h horizon",
    )
    forward.add_argument("--symbol", required=True, choices=("BTCUSDT", "ETHUSDT"))
    verify = commands.add_parser(
        "verify-forward", help="Verify a forward record offline from retained evidence"
    )
    verify.add_argument("--record", type=Path, required=True)
    execution = commands.add_parser(
        "prepare-execution-data", help="Freeze 2024 native 1h execution references"
    )
    execution.add_argument("--output", type=Path, required=True)
    backtest = commands.add_parser(
        "backtest-validation", help="Simulate frozen validation forecasts offline"
    )
    backtest.add_argument("--forecasts", type=Path, required=True)
    backtest.add_argument("--execution", type=Path, required=True)
    backtest.add_argument("--output", type=Path, required=True)
    economics = commands.add_parser(
        "analyse-economics", help="Analyse fixed Stage 2C economics offline"
    )
    economics.add_argument("--backtest", type=Path, required=True)
    economics.add_argument("--output", type=Path, required=True)
    evaluate = commands.add_parser(
        "evaluate-models", help="Evaluate fixed Stage 2B models on validation only"
    )
    evaluate.add_argument(
        "--source", type=Path, default=Path("artifacts/research/stage-2a-v1")
    )
    evaluate.add_argument("--output", type=Path, required=True)
    prepare = commands.add_parser(
        "prepare-research",
        help="Build Stage 2A from the verified frozen export offline",
    )
    prepare.add_argument(
        "--source",
        type=Path,
        default=Path("artifacts/exports/binance-4h-history-v1"),
    )
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--acknowledge-incomplete", action="store_true")
    prepare.add_argument("--settling-seconds", type=int, default=60)
    archive = commands.add_parser(
        "ingest-archive", help="Validate and backfill one monthly archive"
    )
    archive.add_argument("--symbol", required=True, choices=("BTCUSDT", "ETHUSDT"))
    archive.add_argument("--interval", required=True, choices=("1h", "4h"))
    archive.add_argument("--month", required=True)
    archive.add_argument("--dry-run", action="store_true")
    recent = commands.add_parser(
        "sync-recent", help="Sync eligible native 4h REST candles"
    )
    recent.add_argument("--symbol", required=True, choices=("BTCUSDT", "ETHUSDT"))
    recent.add_argument("--interval", required=True, choices=("4h",))
    recent.add_argument(
        "--start",
        type=datetime.fromisoformat,
        help="Explicit UTC 4h boundary, at most 180 days before cutoff",
    )
    recent.add_argument("--settling-seconds", type=int, default=60)
    recent.add_argument("--dry-run", action="store_true")
    review = commands.add_parser(
        "revalidate-history", help="Review up to 30 historical days; no DB writes"
    )
    review.add_argument("--symbol", required=True, choices=("BTCUSDT", "ETHUSDT"))
    review.add_argument("--interval", required=True, choices=("4h",))
    review.add_argument("--start", required=True, type=datetime.fromisoformat)
    review.add_argument("--end", required=True, type=datetime.fromisoformat)
    apply = commands.add_parser(
        "apply-revalidation", help="Apply an explicitly approved retained review"
    )
    apply.add_argument("--plan", required=True, type=Path)
    apply.add_argument("--approve-changes", action="store_true")
    for name in ("backfill-history", "coverage-report", "export-dataset"):
        command = commands.add_parser(name)
        command.add_argument(
            "--symbol",
            required=True,
            choices=("BTCUSDT", "ETHUSDT"),
            **({"nargs": "+"} if name != "backfill-history" else {}),
        )
        command.add_argument("--interval", required=True, choices=("4h",))
        command.add_argument("--start-month", required=True)
        command.add_argument("--end-month", required=True)
        if name == "backfill-history":
            command.add_argument("--dry-run", action="store_true")
            command.add_argument(
                "--allow-source-gaps",
                action="store_true",
                help="Import valid rows and retain source-gap diagnostics",
            )
        if name == "export-dataset":
            command.add_argument("--dataset-id", required=True)
            command.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

    if args.command == "verify-forward":
        from backtest_badger.forward import verify_forward

        try:
            print(json.dumps(verify_forward(args.record), indent=2))
            return 0
        except ValueError as error:
            logger.error("Forward verification failed: %s", error)
        except OSError:
            logger.error(
                "Forward verification failed; check record/training file access."
            )
        return 1

    if args.command == "analyse-economics":
        from backtest_badger.economics import analyse_economics

        try:
            analyse_economics(args.backtest, args.output)
            print(f"Economic diagnostics: {args.output / 'summary.md'}")
            print(f"Analysis manifest: {args.output / 'manifest.json'}")
            return 0
        except ValueError as error:
            logger.error("Economic analysis failed: %s", error)
        except FileExistsError:
            logger.error("Output already exists; choose a new directory.")
        except OSError:
            logger.error("Economic analysis failed; check input/output file access.")
        return 1

    if args.command in ("prepare-execution-data", "backtest-validation"):
        try:
            if args.command == "prepare-execution-data":
                from backtest_badger.execution_data import prepare_execution_data

                prepare_execution_data(args.output)
            else:
                from backtest_badger.backtest import backtest_validation

                backtest_validation(args.forecasts, args.execution, args.output)
                print(f"Historical simulation summary: {args.output / 'summary.md'}")
            print(f"Verified artifact manifest: {args.output / 'manifest.json'}")
            return 0
        except ValueError as error:
            logger.error("Stage 2C failed: %s", error)
        except FileExistsError:
            logger.error("Output already exists; choose a new directory.")
        except OSError:
            logger.error("Stage 2C failed; check input/output file access.")
        return 1

    if args.command == "evaluate-models":
        from backtest_badger.evaluation import evaluate_models

        try:
            evaluate_models(args.source, args.output)
            print(f"Validation summary: {args.output / 'summary.md'}")
            print(f"Experiment manifest: {args.output / 'manifest.json'}")
            return 0
        except ValueError as error:
            logger.error("Model evaluation failed: %s", error)
        except FileExistsError:
            logger.error("Experiment output already exists; choose a new directory.")
        except OSError:
            logger.error("Model evaluation failed; check source/output file access.")
        return 1

    if args.command == "prepare-research":
        try:
            report = prepare_dataset(
                args.source,
                args.output,
                acknowledge_incomplete=args.acknowledge_incomplete,
                settling_seconds=args.settling_seconds,
            )
            print(f"Research manifest: {args.output / 'manifest.json'}")
            print(
                json.dumps(
                    {
                        k: report[k]
                        for k in (
                            "counts",
                            "total_eligible_rows",
                            "sha256",
                            "target_summaries",
                        )
                    },
                    indent=2,
                )
            )
            return 0
        except ValueError as error:
            logger.error("Research preparation failed: %s", error)
        except FileExistsError:
            logger.error("Research output already exists; choose a new directory.")
        except OSError:
            logger.error(
                "Research preparation failed; check source/output file access."
            )
        return 1

    if args.command == "ingest-archive":
        try:
            request = ArchiveRequest(args.symbol, args.interval, args.month)
        except ValueError as error:
            parser.error(str(error))
        if args.dry_run:
            return ingest_archive(request, dry_run=True)

    if args.command in ("backfill-history", "coverage-report", "export-dataset"):
        try:
            if args.command == "backfill-history":
                history_requests(
                    args.symbol, args.interval, args.start_month, args.end_month
                )
            else:
                selections(args.symbol, args.interval, args.start_month, args.end_month)
        except ValueError as error:
            parser.error(str(error))
        if args.command == "backfill-history" and args.dry_run:
            return backfill_history(
                args.symbol,
                args.interval,
                args.start_month,
                args.end_month,
                dry_run=True,
                allow_source_gaps=args.allow_source_gaps,
            )

    try:
        settings = load_settings()
    except ValueError as error:
        logger.error("Configuration error: %s", error)
        return 2

    logging.getLogger().setLevel(settings.log_level)
    if args.command == "record-forward":
        from backtest_badger.forward import record_forward

        try:
            with connect_database(settings) as connection:
                path, record = record_forward(connection, args.symbol)
            print(f"Unscored forward observations: {path}")
            print(
                f"Issued: {record['issued_at']}; "
                f"target: {record['target_close_boundary']}"
            )
            for prediction in record["predictions"]:
                print(
                    f"{prediction['prediction_id']}: "
                    f"{prediction['predicted_log_return_4h']:.17g}"
                )
            return 0
        except FileExistsError as error:
            logger.error("Already recorded; original retained: %s", error)
        except (ValueError, RuntimeError) as error:
            logger.error("Forward recording failed: %s", error)
        except (psycopg.Error, OSError):
            logger.error("Forward recording failed; database/file details suppressed.")
        return 1
    if args.command in ("revalidate-history", "apply-revalidation"):
        try:
            if args.command == "revalidate-history":
                return review_history(
                    args.symbol, settings, start=args.start, end=args.end
                )
            return apply_revalidation(
                args.plan, settings, approve_changes=args.approve_changes
            )
        except ValueError as error:
            logger.error("Revalidation failed: %s", error)
        except (psycopg.Error, OSError, RuntimeError):
            logger.error("Revalidation failed; database/file details suppressed.")
        return 1
    if args.command == "ingest-archive":
        return ingest_archive(request, settings)
    if args.command == "sync-recent":
        try:
            return sync_recent(
                args.symbol,
                settings,
                start=args.start,
                settling_seconds=args.settling_seconds,
                dry_run=args.dry_run,
            )
        except ValueError as error:
            parser.error(str(error))
    if args.command == "backfill-history":
        return backfill_history(
            args.symbol,
            args.interval,
            args.start_month,
            args.end_month,
            settings,
            allow_source_gaps=args.allow_source_gaps,
        )
    if args.command in ("coverage-report", "export-dataset"):
        try:
            with connect_database(settings) as connection:
                selection = (
                    connection,
                    args.symbol,
                    args.interval,
                    args.start_month,
                    args.end_month,
                )
                if args.command == "coverage-report":
                    report = coverage_report(*selection)
                    print(json.dumps(report, indent=2))
                    return 0 if report["complete"] else 1
                report = export_dataset(
                    *selection, args.dataset_id, allow_incomplete=args.allow_incomplete
                )
                print(f"Export: artifacts/exports/{args.dataset_id}/manifest.json")
                print(
                    f"Status: {report['status']}; rows={report['row_counts']}; "
                    f"SHA-256={report['sha256']}"
                )
                return 0
        except ValueError as error:
            logger.error("Research operation failed: %s", error)
        except FileExistsError:
            logger.error("Export already exists; select a new dataset ID.")
        except (psycopg.Error, OSError, RuntimeError):
            logger.error("Research operation failed; database/file details suppressed.")
        return 1
    if args.command == "health":
        print("Application configuration OK.")
        return 0

    try:
        check_database(settings)
    except (psycopg.Error, ValueError):
        # Driver errors can include credentials or connection details. Never print them.
        logger.error(
            "Database health check failed. Check PostgreSQL is running and "
            "POSTGRES_* settings are correct."
        )
        return 1

    print("PostgreSQL connectivity OK.")
    return 0
