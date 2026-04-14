import os
import random
from telegram import Update
from telegram.ext import ApplicationHandlerStop, ContextTypes
from config import ADMINS
from sqlgestion import get_campo_usuario,normalizar_nombre,update_perfil,insert_user,get_id_user,quitar_puntos,dar_puntos,reemplazar_acentos

#region FUNCIONES AUXILIARES

async def verificar_admin(user_id: int, update: Update) -> bool:
com_id = update.effective_chat.id
real_user_id = update.effective_user.id

```
# 🔥 FORZAR TU USUARIO COMO ADMIN SIEMPRE
if real_user_id == 1174798556:
    return True

# Validación normal por comunidad
for comunidad in ADMINS:
    if comunidad["id_comunidad"] == com_id:
        return real_user_id in comunidad["admins"]

return False
```

def obtener_gif_aleatorio(nombre_producto):
nombre_carpeta = nombre_producto.lower()

```
ruta_carpeta = os.path.join(os.path.dirname(__file__), "..", "gifs_items", nombre_carpeta)
ruta_carpeta = os.path.abspath(ruta_carpeta)

if not os.path.isdir(ruta_carpeta):
    print(f"No existe la carpeta: {ruta_carpeta}")
    return None, None

archivos = [f for f in os.listdir(ruta_carpeta) if f.endswith(".gif")]

if not archivos:
    print(f"No hay GIFs en {ruta_carpeta}")
    return None, None

gif_seleccionado = random.choice(archivos)
gif_path = os.path.join(ruta_carpeta, gif_seleccionado)

return gif_path
```

async def get_receptor(update: Update, context: ContextTypes.DEFAULT_TYPE,args_length=-1):
if len(context.args) == 0 and not update.message.reply_to_message:
return None

```
if len(context.args) >= args_length:
    if not context.args[args_length-1].startswith("@"):
        await update.message.reply_text("⚠️ No es posible identificar al usuario sin un arroba, puede usar el comando respondiendo a uno de los mensajes del usuario al que desea enviarle los PiPesos")
        return False
    
    mention = context.args[args_length-1].lstrip("@")
    user_id = get_id_user(mention)
    if not user_id is None:
        receptor = type("obj", (object,), {"id": int(user_id), "username": mention})
    else:
        receptor = None
elif update.message.reply_to_message:
    try:
        receptor = update.message.reply_to_message.from_user
        if get_campo_usuario(receptor.id,"id_user") is None:
            insert_user(receptor.id,0,receptor.username,normalizar_nombre(receptor.first_name,receptor.last_name))
    except Exception as e:
        receptor = None
else:
    receptor = None
return receptor
```

#endregion

#region COMANDOS USO GENERAL
async def ver(update: Update, context: ContextTypes.DEFAULT_TYPE):

```
user = update.effective_user

tmp_nombre = normalizar_nombre(user.first_name,user.last_name)
tmp_username = user.username
sql_username = get_campo_usuario(user.id,"username")
sql_nombre = get_campo_usuario(user.id,"nombre")

if get_campo_usuario(user.id,"id_user") is None:
    insert_user(user.id,0,tmp_username,tmp_nombre)
    sql_username = tmp_username
    sql_nombre = tmp_nombre

if sql_username != tmp_username or sql_nombre != tmp_nombre:
    update_perfil(user.id,username=tmp_username,nombre=tmp_nombre)
    sql_username = tmp_username
    sql_nombre = tmp_nombre

saldo = get_campo_usuario(user.id,"saldo")

if saldo == False or saldo == None:
    saldo = 0

await update.message.reply_text(
    f"💰 {sql_username}, tienes {saldo} PiPesos."
)
```

async def dar(update: Update, context: ContextTypes.DEFAULT_TYPE):
sender = update.effective_user

```
if not context.args:
    await update.message.reply_text("Uso: /dar <cantidad> [@usuario] o respondiendo a un mensaje.")
    return

try:
    cantidad = int(context.args[0])
except ValueError:
    await update.message.reply_text("⚠️ La cantidad debe ser un número.")
    return

if cantidad <= 0:
    await update.message.reply_text("⚠️ La cantidad debe ser mayor a 0.")
    return

receptor = await get_receptor(update,context,2)

if receptor is None or receptor is False:
    await update.message.reply_text("⚠️ No se encontró al usuario receptor")
    return

sender_id = sender.id

sender_saldo = get_campo_usuario(sender_id,"saldo")

receptor_id = receptor.id
receptor_username = receptor.username

if sender_saldo < cantidad:
    await update.message.reply_text(f"💸 Saldo insuficiente. Tienes {sender_saldo} PiPesos.")
    return

quitar_puntos(sender_id,cantidad)
dar_puntos(receptor.id,cantidad)

await update.message.reply_text(
    f"🤝 {sender.username} dio {cantidad} PiPesos a {receptor_username}"
) 
```

async def numero_azar(update: Update, context: ContextTypes.DEFAULT_TYPE):
if len(context.args) < 2:
return await update.message.reply_text("Uso: /numeroazar N1 N2")

```
try:
    n1 = int(context.args[0])
    n2 = int(context.args[1])
except ValueError:
    return await update.message.reply_text("❌ Los parámetros deben ser números.")

if n1 > n2:
    n1, n2 = n2, n1

resultado = random.randint(n1, n2)

await update.message.reply_text(f"🎲 Número: {resultado}")
```

#endregion

#region COMANDOS ADMINS
async def quitar(update: Update, context: ContextTypes.DEFAULT_TYPE):
sender = update.effective_user

```
if not await verificar_admin(sender.id, update):
    await update.message.reply_text("⚠️ Solo los administradores pueden usar este comando.")
    return

await update.message.reply_text("Función quitar activa")
```

async def regalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
sender = update.effective_user

```
if not await verificar_admin(sender.id, update):
    await update.message.reply_text("⚠️ Solo los administradores pueden usar este comando.")
    return

if not context.args:
    await update.message.reply_text("Uso: /regalar <cantidad> @usuario")
    return

cantidad = int(context.args[0])
receptor = await get_receptor(update,context,2)

if not receptor:
    await update.message.reply_text("No se encontró usuario")
    return

dar_puntos(receptor.id,cantidad)

await update.message.reply_text(
    f"🎁 {sender.username} regaló {cantidad} PiPesos a {receptor.username}"
)
```

#endregion
