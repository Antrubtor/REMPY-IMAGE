from typing import Any

import psycopg
from psycopg.rows import dict_row


def connect() -> tuple[psycopg.Connection | None, psycopg.Cursor | None]:
    conn, cur = None, None
    try:
        conn = psycopg.connect("postgresql://postgres:postgres@db:5432/rempy", row_factory=dict_row)
        cur = conn.cursor()
    except (Exception, psycopg.DatabaseError) as error:
        print("Erreur lors de la connexion:", error)
    return conn, cur


def create_table() -> None:
    conn, cur = connect()
    try:
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS benchmarks (
                        id SERIAL PRIMARY KEY,
                        image_hash VARCHAR(64) UNIQUE NOT NULL,
                        image DOUBLE PRECISION[][] NOT NULL,
                        mask DOUBLE PRECISION[][] NOT NULL,
                        image_result DOUBLE PRECISION[][] NOT NULL
                    )
                    """)
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS benchmarks_times (
                        id SERIAL PRIMARY KEY,
                        benchmark_id INTEGER NOT NULL REFERENCES benchmarks(id) ON DELETE CASCADE,
                        time_python DOUBLE PRECISION NOT NULL,
                        time_numba DOUBLE PRECISION NOT NULL
                    )
                    """)
        conn.commit()
    except Exception as error:
        print("Erreur lors de la création de la table", error)

def save_benchmark(image_hash: str, image: list, mask: list, results: dict) -> bool:
    conn, cur = connect()
    try:
        benchmark_id = get_benchmark_id_with_hash_db(image_hash)
        if not benchmark_id:
            cur.execute(
                """
                INSERT INTO benchmarks (image_hash, image, mask, image_result)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (image_hash, image, mask, results.get("image_result"))
            )
            benchmark_id = cur.fetchone()["id"]

        for benchmark in results.get("benchmarks", []):
            cur.execute(
                """
                INSERT INTO benchmarks_times (benchmark_id, time_python, time_numba)
                VALUES (%s, %s, %s)
                """,
                (benchmark_id, benchmark.get("python_time"), benchmark.get("numba_time"))
            )
        conn.commit()
        return True
    except Exception as error:
        print("Erreur lors de la sauvegarde du benchmark", error)
        return False


def get_benchmark(id: int) -> tuple[Any, ...] | None:
    conn, cur = connect()
    try:
        cur.execute("SELECT * FROM benchmarks WHERE id = %s", (id,))
        benchmark_infos = cur.fetchone()
        if not benchmark_infos:
            return None
        print(benchmark_infos)
        cur.execute("SELECT time_python, time_numba FROM benchmarks_times WHERE benchmark_id = %s", (id,))
        benchmark_infos["benchmark_times"] = cur.fetchall()
        return benchmark_infos
    except Exception as error:
        print("Erreur lors de la récupération du benchmark", error)
        return None


def get_all_benchmarks() -> dict[str, list[Any]] | None:
    conn, cur = connect()
    try:
        cur.execute("SELECT * FROM benchmarks")
        benchmarks = cur.fetchall()

        results = []
        for benchmark in benchmarks:
            cur.execute("SELECT time_python, time_numba FROM benchmarks_times WHERE benchmark_id = %s", (benchmark["id"],))
            benchmark["benchmark_times"] = cur.fetchall()
            results.append(benchmark)
        return { "benchmarks": results }
    except Exception as error:
        print("Erreur lors de la récupération des benchmarks", error)
        return None


def get_benchmark_id_with_hash_db(image_hash: str) -> int | None:
    conn, cur = connect()
    try:
        cur.execute("SELECT id FROM benchmarks WHERE image_hash = %s", (image_hash,))
        result = cur.fetchone()
        return result["id"] if result else None
    except Exception as error:
        print("Erreur lors de la récupération de l'id du benchmark avec le hash", error)
        return None

def delete_benchmark(id: int) -> bool:
    conn, cur = connect()
    try:
        cur.execute("DELETE FROM benchmarks WHERE id = %s", (id,))
        conn.commit()
        return True
    except Exception as error:
        print("Erreur lors de la suppression du benchmark", error)
        return False

def delete_all_benchmarks() -> bool:
    conn, cur = connect()
    try:
        cur.execute("DELETE FROM benchmarks")
        conn.commit()
        return True
    except Exception as error:
        print("Erreur lors de la suppression des benchmarks", error)
        return False