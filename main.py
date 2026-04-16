import json
import os
import asyncio
from telegram import ChatPermissions, Update
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

from src.config import BOT_TOKEN, DOMS, obtener_temas_por_comunidad, PUNISHMENT_FILE
from src.database.database import create_database, create_tables, restart_all_combats, _get_connection

from handlers.general import dar, ver, regalar, numero_azar, quitar
from handlers.starting_menu import start, menu_callback
from handlers.tienda import tienda, tienda_callback
from handlers.inventario import inventario, inventario_callback, usar
from handlers.battles import lucha, ataque, aceptar_lucha

from handlers.theme_juegosYcasino import (
    apostar, aceptar, detectar_dado, cancelar_apuesta, jugar, robar
)
from handlers.rewards import manejar_imagenes

from handlers.welcoming import nuevo_usuario, mensaje_de_presentaciones

RUTA_CASTIGADOS = PUNISHMENT_FILE


def cargar_castigados() -> dict:
    if not os.path.exists(RUTA_CASTIGADOS):
        return {}
    try:
        with open(RUTA_CASTIGADOS, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {int(k): set(v) for k, v in data.items()}
    except:
        return {}


def guardar_castigados(data: dict) -> None:
    try:
        serializable = {str(k): list(v) for k, v in data.items()}
        with open(RUTA_CASTIGADOS, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=4, ensure_ascii=False)
    except:
        pass


async def get_theme_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    
    thread_id = update.message.message_thread_id
    chat_id = update.effective_chat.id
    
    await update.message.reply_text(
        f"📌 Chat ID: `{chat_id}`\n"
        f"📌 Theme (message_thread_id): `{thread_id}`",
        parse_mode="Markdown"
    )


async def saludar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mensaje_bienvenida = (
        "🎄✨ *¡Ho, ho, ho! Llegó PiBot al chat* ✨🎄\n"
        "¡Hola a todos! 🤖🎅\n"
        "Estoy aquí para traer *alegría, buena vibra y espíritu navideño*.\n"
    )
    await update.message.reply_text(mensaje_bienvenida, parse_mode="Markdown")


async def castigar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    actor_id = update.effective_user.id

    if chat_id != -1003290179217:
        await update.message.reply_text("❌ Este comando no está habilitado en este grupo.")
        return
    
    if actor_id not in DOMS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    
    from handlers.general import get_receptor
    usuario_objetivo = await get_receptor(update, context, 1)
    
    if usuario_objetivo in (False, None):
        return
    
    target_id = usuario_objetivo.id

    castigados = cargar_castigados()
    castigados.setdefault(chat_id, set()).add(target_id)
    guardar_castigados(castigados)

    await update.message.reply_text("🔇 Usuario castigado.")


async def filtro_castigo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    temas = obtener_temas_por_comunidad(-1003290179217)
    if not temas:
        return
    
    rincon_id = temas.get("theme_rincon")
    castigados = cargar_castigados()

    if chat_id in castigados and user_id in castigados[chat_id]:
        if update.message.message_thread_id != rincon_id:
            try:
                await update.message.delete()
            except:
                pass


async def bloquear_comunidad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat and update.effective_chat.id == -1003397946543:
        raise ApplicationHandlerStop()


# 🔥 ESTE ES EL FIX DEL CONFLICT
async def limpiar_updates(app):
    await app.bot.delete_webhook(drop_pending_updates=True)


def main() -> None:
    create_database()
    create_tables()
    restart_all_combats()

    # 🔥 INSERTAR ITEMS
    conn = _get_connection()
    cursor = conn.cursor()

    print("[INIT] Insertando items tienda...")

    cursor.execute("DELETE FROM items_tb")

    items = [
        ("Collar", 10, "img_items/collar.png", "Un collar elegante", "{user} le coloca un collar a {target} 🐶"),
        ("Latigo", 15, "img_items/latigo.png", "Para castigos", "{user} azota a {target} 🔥"),
        ("Fusta", 12, "img_items/fusta.png", "Castigo elegante", "{user} usa la fusta sobre {target} 😈"),
        ("Galleta", 5, "img_items/galleta.png", "Premio", "{user} le da una galleta a {target} 🍪"),
        ("bola_mordaza", 20, "img_items/bola_mordaza.png", "Silencio", "{user} le pone una mordaza a {target} 🤐"),
        ("sorpresa", 25, "img_items/sorpresa.png", "Sorpresa", "{user} sorprende a {target} 🎁"),
    ]

    for item in items:
        cursor.execute("""
            INSERT INTO items_tb (nombre, precio, imagen, descripcion, mensaje)
            VALUES (?, ?, ?, ?, ?)
        """, item)

    conn.commit()
    conn.close()

    app = Application.builder().token(BOT_TOKEN).build()

    # 🔥 aplicar limpieza
    app.post_init = limpiar_updates

    app.add_handler(MessageHandler(filters.ALL, bloquear_comunidad), group=-1)

    app.add_handler(CommandHandler("start", start), group=0)
    app.add_handler(CommandHandler("castigar", castigar), group=0)

    app.add_handler(CommandHandler("apostar", apostar), group=1)
    app.add_handler(CommandHandler("aceptar", aceptar), group=1)
    app.add_handler(MessageHandler(filters.Dice.DICE, detectar_dado), group=1)

    app.add_handler(CommandHandler("tienda", tienda), group=2)
    app.add_handler(CommandHandler("inventario", inventario), group=2)
    app.add_handler(CommandHandler("ver", ver), group=2)

    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.VIDEO | filters.ANIMATION,
            manejar_imagenes
        ),
        group=3
    )

    app.add_handler(
        CallbackQueryHandler(
            tienda_callback,
            pattern="^(producto_|volver_menu|abrir_tienda|volver_catalogo|comprar_)"
        ),
        group=5
    )

    app.add_handler(MessageHandler(filters.ALL, filtro_castigo), group=6)

    print("🤖 PiBot iniciado...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()