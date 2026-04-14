import os
import random
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMINS
from sqlgestion import get_campo_usuario, normalizar_nombre, update_perfil, insert_user, get_id_user, quitar_puntos, dar_puntos

#region FUNCIONES AUXILIARES

async def verificar_admin(user_id: int, update: Update) -> bool:
    com_id = update.effective_chat.id
    real_user_id = update.effective_user.id

    # FORZAR TU ID COMO ADMIN
    if real_user_id == 1174798556:
        return True

    for comunidad in ADMINS:
        if comunidad["id_comunidad"] == com_id:
            return real_user_id in comunidad["admins"]

    return False

async def get_receptor(update: Update, context: ContextTypes.DEFAULT_TYPE, args_length=-1):
    if len(context.args) == 0 and not update.message.reply_to_message:
        return None
    
    if len(context.args) >= args_length:
        if not context.args[args_length-1].startswith("@"):
            await update.message.reply_text("⚠️ Usa @usuario o responde al mensaje.")
            return False
        
        mention = context.args[args_length-1].lstrip("@")
        user_id = get_id_user(mention)
        if user_id is not None:
            receptor = type("obj", (object,), {"id": int(user_id), "username": mention})
        else:
            receptor = None
    elif update.message.reply_to_message:
        receptor = update.message.reply_to_message.from_user
    else:
        receptor = None

    return receptor

#endregion

#region COMANDOS

async def ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if get_campo_usuario(user.id, "id_user") is None:
        insert_user(user.id, 0, user.username, user.first_name)

    saldo = get_campo_usuario(user.id, "saldo") or 0

    await update.message.reply_text(
        f"💰 {user.username}, tienes {saldo} PiPesos."
    )

async def dar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user

    if not context.args:
        await update.message.reply_text("Uso: /dar <cantidad> @usuario")
        return

    cantidad = int(context.args[0])
    receptor = await get_receptor(update, context, 2)

    if not receptor:
        await update.message.reply_text("No se encontró usuario")
        return

    quitar_puntos(sender.id, cantidad)
    dar_puntos(receptor.id, cantidad)

    await update.message.reply_text(
        f"🤝 {sender.username} dio {cantidad} PiPesos a {receptor.username}"
    )

async def numero_azar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /numeroazar 1 10")
        return

    n1 = int(context.args[0])
    n2 = int(context.args[1])

    resultado = random.randint(n1, n2)

    await update.message.reply_text(f"🎲 Número: {resultado}")

#endregion

#region COMANDOS ADMIN

async def regalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user

    if not await verificar_admin(sender.id, update):
        await update.message.reply_text("⚠️ Solo los administradores pueden usar este comando.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /regalar <cantidad> @usuario")
        return

    cantidad = int(context.args[0])
    receptor = await get_receptor(update, context, 2)

    if not receptor:
        await update.message.reply_text("No se encontró usuario")
        return

    dar_puntos(receptor.id, cantidad)

    await update.message.reply_text(
        f"🎁 {sender.username} regaló {cantidad} PiPesos a {receptor.username}"
    )

async def quitar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user

    if not await verificar_admin(sender.id, update):
        await update.message.reply_text("⚠️ Solo admins")
        return

    await update.message.reply_text("Función quitar activa")

#endregion