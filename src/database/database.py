import re
import sqlite3 as sql
import unicodedata
from typing import Optional, List, Dict, Any

from src.config.settings import DATABASE_FILE


# ================= CORE =================

def _get_connection():
    return sql.connect(DATABASE_FILE)


def create_database():
    conn = _get_connection()
    conn.close()


def create_tables():
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_tb (
            id_user INTEGER PRIMARY KEY,
            saldo INTEGER DEFAULT 0
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfiles_tb (
            id_user INTEGER PRIMARY KEY,
            username TEXT,
            nombre TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items_tb (
            id_item INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            precio INTEGER,
            imagen TEXT,
            descripcion TEXT,
            mensaje TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items_usuarios_tb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER,
            id_item INTEGER,
            cantidad INTEGER DEFAULT 1,
            UNIQUE(id_user, id_item)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS combates_tb (
            id_combate INTEGER PRIMARY KEY AUTOINCREMENT,
            estado TEXT DEFAULT 'activo'
        );
    """)

    conn.commit()
    conn.close()


# ================= USERS =================

def insert_user(id_user, saldo=0, username=None, nombre=None):
    if not nombre:
        return False

    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO usuarios_tb (id_user, saldo) VALUES (?, ?)", (id_user, saldo))
        cursor.execute("INSERT INTO perfiles_tb (id_user, username, nombre) VALUES (?, ?, ?)",
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


def update_perfil(id_user, **datos):
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        columnas = ", ".join([f"{k} = ?" for k in datos.keys()])
        valores = list(datos.values()) + [id_user]

        cursor.execute(f"UPDATE perfiles_tb SET {columnas} WHERE id_user = ?", valores)

        conn.commit()
        conn.close()
        return True
    except:
        return False


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


def dar_puntos(id_user, cantidad):
    saldo = get_campo_usuario(id_user, "saldo") or 0
    return update_saldo(id_user, saldo + cantidad)


def quitar_puntos(id_user, cantidad):
    saldo = get_campo_usuario(id_user, "saldo") or 0
    return update_saldo(id_user, max(0, saldo - cantidad))


# ================= ITEMS =================

def insert_item(nombre, precio, imagen, descripcion=None, mensaje=None):
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO items_tb (nombre, precio, imagen, descripcion, mensaje) VALUES (?, ?, ?, ?, ?)",
            (nombre, precio, imagen, descripcion, mensaje)
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


def update_item(id_item, **datos):
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        columnas = ", ".join([f"{k} = ?" for k in datos.keys()])
        valores = list(datos.values()) + [id_item]

        cursor.execute(f"UPDATE items_tb SET {columnas} WHERE id_item = ?", valores)

        conn.commit()
        conn.close()
        return True
    except:
        return False


def delete_item(id_item):
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items_tb WHERE id_item = ?", (id_item,))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_id_item(nombre):
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
            cursor.execute(
                "UPDATE items_usuarios_tb SET cantidad = ? WHERE id_user = ? AND id_item = ?",
                (r[0] + cantidad, id_user, id_item)
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


# ================= OTROS =================

def delete_user(id_user):
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios_tb WHERE id_user = ?", (id_user,))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_id_user(username):
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id_user FROM perfiles_tb WHERE username = ?", (username,))
        r = cursor.fetchone()
        conn.close()

        return r[0] if r else None
    except:
        return None


def restart_all_combats():
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE combates_tb SET estado = 'cancelado'")
        conn.commit()
        conn.close()
    except:
        pass


# ================= UTILS =================

def normalizar_nombre(nombre, apellido=""):
    texto = f"{nombre} {apellido}".strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r'[^a-zA-Z0-9 ]', '', texto)
    return texto.lower()


def to_plain_text(texto):
    try:
        texto = unicodedata.normalize("NFKD", texto)
        texto = ''.join(c for c in texto if not unicodedata.combining(c))
        texto = re.sub(r'[^a-zA-Z0-9 ]', '', texto)
        return texto.lower().strip()
    except:
        return ""


def reemplazar_acentos(cadena):
    return unicodedata.normalize("NFKD", cadena).encode("ascii", "ignore").decode("utf-8")