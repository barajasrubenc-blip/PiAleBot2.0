import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from config import obtener_temas_por_comunidad
from sqlgestion import normalizar_nombre, get_campo_usuario, insert_user, dar_puntos

contador_imagenes_multimedia = {}
contador_imagenes_nsfw = {}
contador_imagenes_presentacion = []


async def manejar_imagenes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    group_id = update.effective_chat.id
    CHAT_IDS = obtener_temas_por_comunidad(group_id)

    if not CHAT_IDS:
        return  # 🔴 evita que truene todo si no encuentra la comunidad

    thread_id = update.message.message_thread_id

    # MULTIMEDIA
    if CHAT_IDS.get("theme_multimedia") == thread_id:
        await detectar_imagenes_multimedia(update, context)
        return

    # PRESENTACIONES
    if group_id != -1003290179217:
        if CHAT_IDS.get("theme_presentaciones") == thread_id:
            await detectar_imagen_presentacion(update, context)
            return
    else:
        if thread_id is None:
            await detectar_imagen_presentacion(update, context)
            return

    # NSFW
    if CHAT_IDS.get("theme_NSFW") == thread_id:
        await detectar_imagenes_nsfw(update, context)
        return

    # EXHIBICIONISMO
    if CHAT_IDS.get("theme_Exhibicionismo") == thread_id:
        await detectar_exhibicion(update, context)
        return


async def detectar_imagen_presentacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    thread_id = getattr(msg, "message_thread_id", None)

    tiene_photo = bool(msg.photo)
    tiene_document_image = False

    if msg.document and getattr(msg.document, "mime_type", ""):
        if msg.document.mime_type.startswith("image/"):
            tiene_document_image = True

    if not (tiene_photo or tiene_document_image):
        return

    user = msg.from_user
    user_id = user.id
    username = user.username
    nombre = normalizar_nombre(user.first_name, user.last_name)

    if user_id in contador_imagenes_presentacion:
        return

    if get_campo_usuario(user_id, "id_user") is None:
        insert_user(user_id, 0, username, nombre)

    contador_imagenes_presentacion.append(user_id)
    dar_puntos(user_id, 5)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"📸 {username or nombre}, gracias por presentarte con imagen 😁 como recompensa, te hemos otorgado tus primeros 5 pipesos 🌟",
        message_thread_id=thread_id
    )


async def detectar_imagenes_multimedia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.message
    if not mensaje:
        return

    tiene_foto = bool(mensaje.photo)
    tiene_video = bool(mensaje.video)
    tiene_gif = bool(mensaje.animation)

    if not (tiene_foto or tiene_video or tiene_gif):
        return

    thread_id = mensaje.message_thread_id
    user = mensaje.from_user

    user_id = user.id
    username = user.username
    nombre = normalizar_nombre(user.first_name, user.last_name)

    if user_id not in contador_imagenes_multimedia:
        contador_imagenes_multimedia[user_id] = 0

    contador_imagenes_multimedia[user_id] += 1

    if contador_imagenes_multimedia[user_id] >= 3:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🎉 @{username or nombre} recibió 10 PiPesos por multimedia",
            message_thread_id=thread_id
        )

        if get_campo_usuario(user_id, "id_user") is None:
            insert_user(user_id, 0, username, nombre)

        dar_puntos(user_id, 10)
        contador_imagenes_multimedia[user_id] = 0

    async def resetear():
        await asyncio.sleep(120)
        contador_imagenes_multimedia[user_id] = 0

    asyncio.create_task(resetear())


async def detectar_imagenes_nsfw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.message
    if not mensaje:
        return

    tiene_foto = bool(mensaje.photo)
    tiene_video = bool(mensaje.video)
    tiene_gif = bool(mensaje.animation)

    if not (tiene_foto or tiene_video or tiene_gif):
        return

    thread_id = mensaje.message_thread_id
    user = mensaje.from_user

    user_id = user.id
    username = user.username
    nombre = normalizar_nombre(user.first_name, user.last_name)

    if user_id not in contador_imagenes_nsfw:
        contador_imagenes_nsfw[user_id] = 0

    contador_imagenes_nsfw[user_id] += 1

    if contador_imagenes_nsfw[user_id] >= 5:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🔥 @{username or nombre} recibió 16 PiPesos en NSFW",
            message_thread_id=thread_id
        )

        if get_campo_usuario(user_id, "id_user") is None:
            insert_user(user_id, 0, username, nombre)

        dar_puntos(user_id, 16)
        contador_imagenes_nsfw[user_id] = 0

    async def resetear():
        await asyncio.sleep(120)
        contador_imagenes_nsfw[user_id] = 0

    asyncio.create_task(resetear())


async def detectar_exhibicion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.message
    if not mensaje:
        return

    tiene_foto = bool(mensaje.photo)
    tiene_video = bool(mensaje.video)
    tiene_gif = bool(mensaje.animation)

    if not (tiene_foto or tiene_video or tiene_gif):
        return

    thread_id = mensaje.message_thread_id
    user = mensaje.from_user

    user_id = user.id
    username = user.username
    nombre = normalizar_nombre(user.first_name, user.last_name)

    if get_campo_usuario(user_id, "id_user") is None:
        insert_user(user_id, 0, username, nombre)

    dar_puntos(user_id, 10)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✨ @{username or nombre} recibió 10 PiPesos en Exhibicionismo",
        message_thread_id=thread_id
    )