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
                time DOUBLE PRECISION NOT NULL
            )
        """)
    except Exception as error:
        print("Erreur lors de la création de la table", error)
    conn.commit()

def delete_all_benchmarks() -> bool:
    conn, cur = connect()
    try:
        cur.execute("DELETE FROM benchmarks")
        conn.commit()
        return True
    except Exception as error:
        print("Erreur lors de la suppression des benchmarks", error)
        return False

def get_benchmark_if_exist(image_hash: str) -> tuple[Any, ...] | None:
    conn, cur = connect()
    try:
        cur.execute("SELECT * FROM benchmarks WHERE image_hash = %s", (image_hash,))
        return cur.fetchone()
    except Exception as error:
        print("Erreur lors de la vérification du benchmark", error)
    return None



def save_benchmark(image_hash: str, time: float) -> bool:
    conn, cur = connect()
    try:
        cur.execute(
            """
            INSERT INTO benchmarks (image_hash, time)
            VALUES (%s, %s)
            """,
            (image_hash, time)
        )
        conn.commit()
        return True
    except Exception as error:
        print("Erreur lors de la sauvegarde du benchmark", error)
        return False


def get_all_benchmarks() -> list[dict] | None:
    conn, cur = connect()
    try:
        cur.execute("SELECT * FROM benchmarks")
        return cur.fetchall()
    except Exception as error:
        print("Erreur lors de la récupération des benchmarks", error)
        return None