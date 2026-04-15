import re
import sqlite3 as sql
import unicodedata
from typing import Optional, Dict, List, Any

from src.config import DATABASE_FILE


def create_database() -> None:
    conn = sql.connect(DATABASE_FILE)
    conn.commit()
    conn.close()


def create_tables() -> None:
    conn = sql.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_tb (
            id_user INTEGER PRIMARY KEY,
            saldo INTEGER DEFAULT 0
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items_tb (
            id_item INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            precio INTEGER NOT NULL,
            imagen TEXT NOT NULL,
            descripcion TEXT,
            mensaje TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items_usuarios_tb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER NOT NULL,
            id_item INTEGER NOT NULL,
            cantidad INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (id_user) REFERENCES usuarios_tb(id_user) ON DELETE CASCADE,
            FOREIGN KEY (id_item) REFERENCES items_tb(id_item) ON DELETE CASCADE,
            UNIQUE(id_user, id_item)
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuario ON items_usuarios_tb(id_user);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_item ON items_usuarios_tb(id_item);")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfiles_tb (
            id_user INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            nombre TEXT NOT NULL,
            rol TEXT,
            orientacion_sexual TEXT,
            genero TEXT,
            ubicacion TEXT,
            edad INTEGER,
            FOREIGN KEY (id_user) REFERENCES usuarios_tb(id_user) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS combates_tb (
            id_combate INTEGER PRIMARY KEY AUTOINCREMENT,
            id_atacante INTEGER NOT NULL,
            id_defensor INTEGER NOT NULL,
            username_atacante TEXT NOT NULL,
            username_defensor TEXT NOT NULL,
            apuesta INTEGER NOT NULL DEFAULT 0,
            hp_atacante INTEGER NOT NULL DEFAULT 20,
            hp_defensor INTEGER NOT NULL DEFAULT 20,
            turno INTEGER NOT NULL DEFAULT 1,
            es_turno_atacante INTEGER NOT NULL DEFAULT 1,
            estado TEXT NOT NULL DEFAULT 'activo',
            ganador INTEGER,
            fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()


def _get_connection():
    return sql.connect(DATABASE_FILE)


# ================= USERS =================

def insert_user(id_user, saldo=0, username=None, nombre=None):
    if not nombre:
        return False

    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO usuarios_tb (id_user, saldo) VALUES (?, ?);", (id_user, saldo))
        cursor.execute("INSERT INTO perfiles_tb (id_user, username, nombre) VALUES (?, ?, ?);",
                       (id_user, username, nombre))

        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_campo_usuario(id_user, columna):
    tabla = "usuarios_tb" if columna == "saldo" else "perfiles_tb"

    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {columna} FROM {tabla} WHERE id_user = ?", (id_user,))
        r = cursor.fetchone()
        conn.close()
        return r[0] if r else None
    except:
        return None


def dar_puntos(id_user, cantidad):
    saldo = get_campo_usuario(id_user, "saldo") or 0
    return update_saldo(id_user, saldo + cantidad)


def quitar_puntos(id_user, cantidad):
    saldo = get_campo_usuario(id_user, "saldo") or 0
    return update_saldo(id_user, max(0, saldo - cantidad))


def update_saldo(id_user, saldo):
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios_tb SET saldo = ? WHERE id_user = ?", (saldo, id_user))
        conn.commit()
        conn.close()
        return True
    except:
        return False


# ================= ITEMS =================

def insert_item(nombre, precio, ruta_imagen, descripcion=None, mensaje=None):
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO items_tb (nombre, precio, imagen, descripcion, mensaje) VALUES (?, ?, ?, ?, ?)",
            (nombre, precio, ruta_imagen, descripcion, mensaje)
        )

        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_campo_item(id_item, columna):
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {columna} FROM items_tb WHERE id_item = ?", (id_item,))
        r = cursor.fetchone()
        conn.close()
        return r[0] if r else None
    except:
        return None


def get_id_item(nombre):
    nombre = normalizar_nombre(nombre).capitalize()

    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_item FROM items_tb WHERE nombre = ?", (nombre,))
        r = cursor.fetchone()
        conn.close()
        return r[0] if r else None
    except:
        return None


# ================= INVENTARIO =================

def insert_user_item(id_user, id_item, cantidad=1):
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT cantidad FROM items_usuarios_tb WHERE id_user = ? AND id_item = ?",
            (id_user, id_item)
        )
        r = cursor.fetchone()

        if r:
            nueva = r[0] + cantidad
            cursor.execute(
                "UPDATE items_usuarios_tb SET cantidad = ? WHERE id_user = ? AND id_item = ?",
                (nueva, id_user, id_item)
            )
        else:
            cursor.execute(
                "INSERT INTO items_usuarios_tb (id_user, id_item, cantidad) VALUES (?, ?, ?)",
                (id_user, id_item, cantidad)
            )

        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_items(id_user):
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT items_tb.id_item, items_tb.nombre, items_tb.precio,
                   items_tb.imagen, items_usuarios_tb.cantidad
            FROM items_usuarios_tb
            INNER JOIN items_tb ON items_tb.id_item = items_usuarios_tb.id_item
            WHERE items_usuarios_tb.id_user = ?
        """, (id_user,))

        filas = cursor.fetchall()
        conn.close()

        return [
            {
                "id_item": f[0],
                "nombre": f[1],
                "precio": f[2],
                "imagen": f[3],
                "cantidad": f[4]
            } for f in filas
        ]
    except:
        return []


def get_cantidad_item_inventario(id_user, id_item):
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT cantidad FROM items_usuarios_tb WHERE id_user = ? AND id_item = ?",
            (id_user, id_item)
        )

        r = cursor.fetchone()
        conn.close()
        return r[0] if r else 0
    except:
        return 0


def update_cantidad(user_id, item_id, cantidad):
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE items_usuarios_tb SET cantidad = ? WHERE id_user = ? AND id_item = ?",
            (cantidad, user_id, item_id)
        )

        conn.commit()
        conn.close()
        return True
    except:
        return False


def delete_item_user(id_user, id_item):
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM items_usuarios_tb WHERE id_user = ? AND id_item = ?",
            (id_user, id_item)
        )

        conn.commit()
        conn.close()
        return True
    except:
        return False


# ================= UTILS =================

def normalizar_nombre(nombre, apellido=""):
    texto = f"{nombre} {apellido}".strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r'[^a-zA-Z0-9 ]', '', texto)
    return texto.lower()


def restart_all_combats():
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE combates_tb SET estado = 'cancelado' WHERE estado = 'activo'"
        )

        conn.commit()
        conn.close()
    except:
        pass