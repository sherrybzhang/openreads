import csv
import os
from typing import Optional, Protocol, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text


class _SessionLike(Protocol):
    def execute(self, statement: object, params: object = None) -> object:
        ...

    def rollback(self) -> None:
        ...


def get_database_url() -> str:
    """
    Return the database URL from environment or a local default.

    Returns:
        The database connection URL.
    """
    return os.environ.get("DATABASE_URL", "postgresql://localhost/sherryzhang")


def log_error(error_log_path: str, message: str) -> None:
    """
    Append a single error message to the error log file.

    Args:
        error_log_path: Path to the error log file.
        message: Error message to append.
    """
    with open(error_log_path, "a", encoding="utf-8") as f:
        f.write(message + "")


def insert_batch(
    db: _SessionLike, batch_params: list[dict[str, str]], batch_rows: list[int], error_log_path: str
) -> Tuple[int, int, int]:
    """
    Insert a batch of book rows; fall back to per-row inserts on batch failure.

    Args:
        db: SQLAlchemy session.
        batch_params: List of row parameter dicts.
        batch_rows: CSV row numbers matching batch_params.
        error_log_path: Path to the error log file.

    Returns:
        A tuple of (inserted, skipped, errors).
    """
    inserted = 0
    skipped = 0
    errors = 0

    if not batch_params:
        return inserted, skipped, errors

    # Fast path: attempt batch insert for performance
    try:
        db.execute(
            text(
                "INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"
            ),
            batch_params,
        )
        inserted += len(batch_params)
        return inserted, skipped, errors
    except Exception as exc:
        db.rollback()
        log_error(error_log_path, f"Batch insert failed: {exc}")

    # Fallback to per-row inserts to isolate errors
    for params, row_index in zip(batch_params, batch_rows, strict=False):
        try:
            db.execute(
                text(
                    "INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"
                ),
                params,
            )
            inserted += 1
        except Exception as row_exc:
            db.rollback()
            skipped += 1
            errors += 1
            log_error(error_log_path, f"Skipping row {row_index}: {row_exc}")

    return inserted, skipped, errors


def load_books(
    csv_path: str, batch_size: int = 500, error_log_path: Optional[str] = None
) -> Tuple[int, int, int]:
    """
    Load books from a CSV into the database with batching and error logging.

    Args:
        csv_path: Path to the CSV file.
        batch_size: Number of rows per batch insert.
        error_log_path: Optional path for error logs.

    Returns:
        A tuple of (inserted, skipped, errors).
    """
    engine = create_engine(get_database_url())
    db = scoped_session(sessionmaker(bind=engine))

    inserted = 0
    skipped = 0
    errors = 0

    if error_log_path is None:
        error_log_path = os.path.join(os.path.dirname(__file__), "import_errors.log")

    try:
        with open(csv_path, newline="") as f:
            reader = csv.reader(f)
            batch_params = []
            batch_rows = []

            # Stream rows and accumulate batches
            for row_index, row in enumerate(reader, start=1):
                if not row:
                    continue

                # Skip header row if present
                if row[0].strip().lower() == "isbn":
                    continue

                if len(row) < 4:
                    skipped += 1
                    log_error(
                        error_log_path,
                        f"Skipping row {row_index}: not enough columns",
                    )
                    continue

                isbn, title, author, year = (cell.strip() for cell in row[:4])
                params = {"isbn": isbn, "title": title, "author": author, "year": year}

                batch_params.append(params)
                batch_rows.append(row_index)

                # Flush when batch is full
                if len(batch_params) >= batch_size:
                    ins, skp, err = insert_batch(
                        db, batch_params, batch_rows, error_log_path
                    )
                    inserted += ins
                    skipped += skp
                    errors += err
                    batch_params = []
                    batch_rows = []

            # Flush remaining
            ins, skp, err = insert_batch(db, batch_params, batch_rows, error_log_path)
            inserted += ins
            skipped += skp
            errors += err

        db.commit()
    finally:
        db.remove()

    return inserted, skipped, errors


def main() -> None:
    """Entrypoint to load books from the default CSV path."""
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "books.csv")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"CSV file not found: {data_path}")

    inserted, skipped, errors = load_books(data_path)
    print(
        "Import complete. "
        f"Inserted: {inserted}, Skipped: {skipped}, Errors: {errors}"
    )


if __name__ == "__main__":
    main()
