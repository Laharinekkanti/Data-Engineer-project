
import argparse
import csv
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR.parent / "data"

MOVIES_CSV = DATA_DIR / "movies.csv"
RATINGS_CSV = DATA_DIR / "ratings.csv"

DATABASE_FILE = PROJECT_DIR / "movie_data.db"
SCHEMA_FILE = PROJECT_DIR / "schema.sql"

OMDB_URL = "https://www.omdbapi.com/"


class APIQuotaReached(Exception):
    pass


def get_connection():
    connection = sqlite3.connect(DATABASE_FILE)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_tables(connection):
    schema = SCHEMA_FILE.read_text(encoding="utf-8")
    connection.executescript(schema)
    connection.commit()


def extract_year(title):
    match = re.search(r"\((\d{4})\)\s*$", title)
    return int(match.group(1)) if match else None


def clean_title(title):
    return re.sub(r"\s*\(\d{4}\)\s*$", "", title).strip()


def parse_genres(genre_text):
    if not genre_text or genre_text == "(no genres listed)":
        return []

    return [
        genre.strip()
        for genre in genre_text.split("|")
        if genre.strip()
    ]


def fetch_omdb_details(title, year, api_key):
    if not api_key:
        return None

    params = {"apikey": api_key, "t": title}

    if year:
        params["y"] = year

    try:
        response = requests.get(
            OMDB_URL,
            params=params,
            timeout=15
        )

        response.raise_for_status()
        result = response.json()

        if result.get("Response") == "False":
            error = result.get("Error", "")

            if "Request limit reached" in error or "Invalid API key" in error:
                raise APIQuotaReached(error)

            print(f"OMDb did not find: {title} ({year or 'year unknown'})")
            return None

        return {
            "director": result.get("Director"),
            "plot": result.get("Plot"),
            "box_office": result.get("BoxOffice"),
            "imdb_rating": result.get("imdbRating"),
        }

    except APIQuotaReached:
        raise

    except requests.RequestException as error:
        print(f"OMDb request failed for '{title}': {error}")

    except ValueError:
        print(f"OMDb returned invalid JSON for: {title}")

    return None


def save_movie(connection, movie_id, title, year):
    connection.execute(
        """
        INSERT INTO movies (movie_id, title, release_year)
        VALUES (?, ?, ?)
        ON CONFLICT(movie_id) DO UPDATE SET
            title = excluded.title,
            release_year = excluded.release_year
        """,
        (movie_id, title, year)
    )


def save_genres(connection, movie_id, genre_names):
    for genre_name in genre_names:
        connection.execute(
            "INSERT OR IGNORE INTO genres (genre_name) VALUES (?)",
            (genre_name,)
        )

        genre_row = connection.execute(
            "SELECT genre_id FROM genres WHERE genre_name = ?",
            (genre_name,)
        ).fetchone()

        connection.execute(
            """
            INSERT OR IGNORE INTO movie_genres (movie_id, genre_id)
            VALUES (?, ?)
            """,
            (movie_id, genre_row[0])
        )


def save_omdb_details(connection, movie_id, details):
    if not details:
        return

    connection.execute(
        """
        INSERT INTO omdb_details
            (movie_id, director, plot, box_office, imdb_rating)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(movie_id) DO UPDATE SET
            director = excluded.director,
            plot = excluded.plot,
            box_office = excluded.box_office,
            imdb_rating = excluded.imdb_rating
        """,
        (
            movie_id,
            details["director"],
            details["plot"],
            details["box_office"],
            details["imdb_rating"]
        )
    )


def load_movies(connection, limit=None, skip_api=False):
    if not MOVIES_CSV.exists():
        raise FileNotFoundError(
            f"Cannot find {MOVIES_CSV}. Put the full movies.csv in the data folder."
        )

    api_key = os.getenv("OMDB_API_KEY", "").strip()

    if not skip_api and not api_key:
        raise ValueError(
            "OMDB_API_KEY is missing. Set it before running the ETL, "
            "or use --skip-api."
        )

    processed = 0

    with MOVIES_CSV.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if limit is not None and processed >= limit:
                break

            movie_id = int(row["movieId"])
            original_title = row["title"].strip()
            title = clean_title(original_title)
            year = extract_year(original_title)
            genres = parse_genres(row.get("genres", ""))

            save_movie(connection, movie_id, title, year)
            save_genres(connection, movie_id, genres)

            already_enriched = connection.execute(
                "SELECT 1 FROM omdb_details WHERE movie_id = ?",
                (movie_id,)
            ).fetchone()

            if not skip_api and not already_enriched:
                try:
                    details = fetch_omdb_details(title, year, api_key)
                    save_omdb_details(connection, movie_id, details)
                    time.sleep(0.25)

                except APIQuotaReached as error:
                    print(f"\nOMDb API stopped: {error}")
                    print("Continuing ETL without further OMDb requests.")
                    skip_api = True

            processed += 1

            if processed % 100 == 0:
                connection.commit()
                print(f"Processed {processed} movies...")

    connection.commit()
    print(f"Movie records processed: {processed}")


def load_ratings(connection):
    if not RATINGS_CSV.exists():
        raise FileNotFoundError(
            f"Cannot find {RATINGS_CSV}. Put the full ratings.csv in the data folder."
        )

    processed = 0

    with RATINGS_CSV.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            user_id = int(row["userId"])
            movie_id = int(row["movieId"])
            rating = float(row["rating"])
            timestamp_value = int(row["timestamp"])

            rated_at = datetime.fromtimestamp(
                timestamp_value,
                tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S")

            movie_exists = connection.execute(
                "SELECT 1 FROM movies WHERE movie_id = ?",
                (movie_id,)
            ).fetchone()

            if movie_exists:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO ratings
                        (user_id, movie_id, rating, rated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, movie_id, rating, rated_at)
                )

            processed += 1

            if processed % 10000 == 0:
                connection.commit()
                print(f"Processed {processed} ratings...")

    connection.commit()
    print(f"Rating rows processed: {processed}")


def print_summary(connection):
    tables = [
        "movies",
        "ratings",
        "genres",
        "movie_genres",
        "omdb_details"
    ]

    print("\nDATABASE SUMMARY")
    print("----------------")

    for table in tables:
        count = connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(f"{table}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Run the MovieLens ETL pipeline."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N movies."
    )

    parser.add_argument(
        "--skip-api",
        action="store_true",
        help="Skip OMDb enrichment and load MovieLens data only."
    )

    args = parser.parse_args()

    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be zero or a positive number.")

    connection = get_connection()

    try:
        create_tables(connection)

        print("Step 1: Loading movie data...")

        load_movies(
            connection,
            limit=args.limit,
            skip_api=args.skip_api
        )

        print("\nStep 2: Loading ratings data...")

        load_ratings(connection)

        print_summary(connection)

        print("\nETL pipeline completed.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
