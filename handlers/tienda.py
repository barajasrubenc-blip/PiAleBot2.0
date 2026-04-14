import os
from telegram import InputMediaPhoto, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlgestion import get_campo_usuario, get_campo_item, quitar_puntos,insert_user_item,get_cantidad_item_inventario,update_cantidad
from telegram.error import TelegramError

# ==============================
#   TIENDA (Pantalla inicial)
# ==============================
async def tienda(update: Update, context: ContextTypes.DEFAULT_TYPE, from_menu=False):
    user_id = update.effective_user.id
    chat = update.effective_chat

    if chat.type != "private":
        deep_link = f"https://t.me/PiBotBotBotBotBot?start=menu"
        keyboard = [[InlineKeyboardButton("✨ Abrir menú principal", url=deep_link)]]

        await update.message.reply_text(
            "🛍️ La tienda solo está disponible en el chat privado.\n"
            "Haz clic en el botón para abrir el menú principal:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if get_campo_usuario(user_id, "id_user") is None:
        await update.message.reply_text(
            "⚠️ No estás registrado.\nUsa /ver en el chat general de la comunidad para registrarte primero."
        )
        return

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RUTA_CATALOGO = os.path.join(BASE_DIR, "img_items", "catalogo.png")

    if from_menu:
        await update.callback_query.message.edit_media(
            media=InputMediaPhoto(open(RUTA_CATALOGO, "rb"))
        )
        await update.callback_query.message.edit_caption(
            caption="🛍️ **Catálogo de productos**",
            parse_mode="Markdown",
            reply_markup=botonera_catalogo()
        )
        return

    await update.message.reply_photo(
        photo=open(RUTA_CATALOGO, "rb"),
        caption="🛍️ **Catálogo de productos**",
        parse_mode="Markdown",
        reply_markup=botonera_catalogo()
    )

# ==============================
#   CALLBACKS
# ==============================
def main_menu_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Ver comandos", callback_data="ver_comandos")],
        [InlineKeyboardButton("📦 Ver inventario", callback_data="ver_inventario")],
        [InlineKeyboardButton("👤 Perfil", callback_data="perfil")]
    ])

async def tienda_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "volver_menu":
        try:
            await query.edit_message_text(
                "✨ *Menú principal*\nSelecciona una opción:",
                parse_mode="Markdown",
                reply_markup=main_menu_markup()
            )
            return
        except TelegramError:
            try:
                await context.bot.send_message(
                    chat_id=query.from_user.id,
                    text="✨ *Menú principal*\nSelecciona una opción:",
                    parse_mode="Markdown",
                    reply_markup=main_menu_markup()
                )
            except Exception as e:
                print("Error enviando menu fallback:", e)

            try:
                await query.message.delete()
            except Exception:
                pass
            return

    if data.startswith("producto_"):
        id_item = int(data.replace("producto_", ""))
        descripcion = get_campo_item(id_item, "descripcion")
        await mostrar_item(id_item, descripcion, update, context)
        return

    if data == "volver_catalogo":
        await volver_catalogo(update, context)
        return

    if data.startswith("comprar_"):
        id_item = int(data.replace("comprar_", ""))
        await comprar_item(id_item, update, context)
        return

# ==============================
#       VOLVER AL CATÁLOGO
# ==============================
async def volver_catalogo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RUTA_CATALOGO = os.path.join(BASE_DIR, "img_items", "catalogo.png")

    with open(RUTA_CATALOGO, "rb") as img:
        await query.edit_message_media(media=InputMediaPhoto(img))

    await query.edit_message_caption(
        caption="🛍️ **Catálogo de productos**",
        parse_mode="Markdown",
        reply_markup=botonera_catalogo()
    )

# ==============================
#     COMPRAR ITEM
# ==============================
async def comprar_item(id_item, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    item_nombre = get_campo_item(id_item, "nombre")
    item_precio = int(get_campo_item(id_item, "precio"))

    try:
        saldo_usuario = int(get_campo_usuario(user_id, "saldo"))
    except:
        saldo_usuario = 0

    if saldo_usuario < item_precio:
        await query.edit_message_caption(
            caption=(
                f"❌ *No tienes suficientes PiPesos*\n\n"
                f"Item: *{item_nombre}*\n"
                f"Precio: `{item_precio}`\n"
                f"Tu saldo actual: `{saldo_usuario}`"
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Volver al catálogo", callback_data="volver_catalogo")]
            ])
        )
        return

    await query.edit_message_caption(
        caption=(
            f"🎉 *¡Compra exitosa!*\n\n"
            f"Has comprado: *{item_nombre}*\n"
            f"Precio: `{item_precio}`\n\n"
            f"💼 El item ha sido añadido a tu inventario."
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Volver al catálogo", callback_data="volver_catalogo")]
        ])
    )

    quitar_puntos(user_id,item_precio)
    cantidad_actual = get_cantidad_item_inventario(user_id,id_item)

    if cantidad_actual == 0:
        insert_user_item(user_id,id_item,cantidad_actual+1)
    else:
        update_cantidad(user_id,id_item,cantidad_actual+1)

# ==============================
#    MOSTRAR ITEM ESPECÍFICO
# ==============================
async def mostrar_item(id_item, descripcion, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    item_nombre = get_campo_item(id_item, "nombre")
    item_precio = get_campo_item(id_item, "precio")
    item_imagen = get_campo_item(id_item, "imagen")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if not item_imagen:
        ruta_absoluta_imagen = os.path.join(BASE_DIR, "img_items", "catalogo.png")
    else:
        ruta_absoluta_imagen = os.path.join(BASE_DIR, item_imagen)

    texto_item = (
        f"📦 *{item_nombre}*\n"
        f"💬 {descripcion}\n"
        f"💲 Precio: {item_precio} COP"
    )

    botonera = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Volver al catálogo", callback_data="volver_catalogo")],
        [InlineKeyboardButton("🛒 Comprar", callback_data=f"comprar_{id_item}")]
    ])

    with open(ruta_absoluta_imagen, "rb") as img:
        await query.edit_message_media(media=InputMediaPhoto(img))

    await query.edit_message_caption(
        caption=texto_item,
        parse_mode="Markdown",
        reply_markup=botonera
    )

# ==============================
#   BOTONERA CATÁLOGO
# ==============================
def botonera_catalogo():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1️⃣ Collar", callback_data="producto_1"),
            InlineKeyboardButton("2️⃣ Látigo", callback_data="producto_2"),
            InlineKeyboardButton("3️⃣ Fusta", callback_data="producto_3"),
        ],
        [
            InlineKeyboardButton("4️⃣ Galleta", callback_data="producto_4"),
            InlineKeyboardButton("5️⃣ Bola mordaza", callback_data="producto_5"),
            InlineKeyboardButton("6️⃣ ???", callback_data="producto_6"),
        ],
        [
            InlineKeyboardButton("⬅️ Volver al menú", callback_data="volver_menu")
        ]
    ])