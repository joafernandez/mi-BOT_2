import logging
import mysql.connector
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Conexión a la base de datos
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",  # Cambiar si usás contraseña
    database="mi_base"
)

# Estados
ELEGIR, BUSCAR_NOMBRE, BUSCAR_CODIGO, BUSCAR_ZONA, ELEGIR_UNIDAD = range(5)

# Logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Menú principal
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola, soy tu bot de consulta. ¿En qué unidad estás interesada?\n"
        "1) Buscar por nombre\n"
        "2) Buscar por código\n"
        "3) Buscar por zona (provincia) \n"
        "4) No, ya terminé"
    )
    return ELEGIR

# Elegir opción
async def elegir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    opcion = update.message.text.strip()
    if opcion == "1":
        await update.message.reply_text("Ingrese el nombre de la unidad:")
        return BUSCAR_NOMBRE
    elif opcion == "2":
        await update.message.reply_text("Ingrese el código de la unidad:")
        return BUSCAR_CODIGO
    elif opcion == "3":
        await update.message.reply_text("Ingrese la zona o provincia:")
        return BUSCAR_ZONA
    elif opcion == "4":
        await update.message.reply_text("¡Me alegro! Vuelve pronto escribiendo /start para usar cualquiera de las 3 opciones 😊")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Opción no válida. Intente con 1, 2, 3 o 4.")
        return ELEGIR

# Buscar por nombre
async def buscar_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.text.strip()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM unidades WHERE nombre LIKE %s", (f"%{nombre}%",))
    result = cursor.fetchone()
    if result:
        codigo, nombre, zona, jefe = result[1], result[2], result[3], result[4]
        await update.message.reply_text(
            f"✅ Información de la unidad {nombre}:\n"
            f"- Código: {codigo}\n- Zona: {zona}\n- Jefe: {jefe}"
        )
    else:
        await update.message.reply_text("No se encontró ninguna unidad con ese nombre.")
    await update.message.reply_text(
        "¿Desea hacer otra consulta?\n"
        "1) Buscar por nombre\n"
        "2) Buscar por código\n"
        "3) Buscar por zona\n"
        "4) No, ya terminé"
    )
    return ELEGIR

# Buscar por código
async def buscar_codigo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    codigo = update.message.text.strip()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM unidades WHERE codigo = %s", (codigo,))
    result = cursor.fetchone()
    if result:
        codigo, nombre, zona, jefe = result[1], result[2], result[3], result[4]
        await update.message.reply_text(
            f"✅ Información del código {codigo}:\n"
            f"- Unidad: {nombre}\n- Zona: {zona}\n- Jefe: {jefe}"
        )
    else:
        await update.message.reply_text("No se encontró ninguna unidad con ese código.")
    await update.message.reply_text(
        "¿Desea hacer otra consulta?\n"
        "1) Buscar por nombre\n"
        "2) Buscar por código\n"
        "3) Buscar por zona\n"
        "4) No, ya terminé"
    )
    return ELEGIR

# Buscar por zona
async def buscar_zona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    zona = update.message.text.strip()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM unidades WHERE zona LIKE %s", (f"%{zona}%",))
    results = cursor.fetchall()
    if results:
        context.user_data["resultados"] = results
        mensaje = "📍 Unidades en esa zona:\n"
        for idx, r in enumerate(results, start=1):
            mensaje += f"{idx}) {r[2]}\n"
        mensaje += "Elija la unidad (1, 2, etc):"
        await update.message.reply_text(mensaje)
        return ELEGIR_UNIDAD
    else:
        await update.message.reply_text("No se encontraron unidades en esa zona.")
        await update.message.reply_text(
            "¿Desea hacer otra consulta?\n"
            "1) Buscar por nombre\n"
            "2) Buscar por código\n"
            "3) Buscar por zona\n"
            "4) No, ya terminé"
        )
        return ELEGIR

# Elegir unidad dentro de la zona
async def elegir_unidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        indice = int(update.message.text.strip()) - 1
        datos = context.user_data["resultados"][indice]
        codigo, nombre, zona, jefe = datos[1], datos[2], datos[3], datos[4]
        await update.message.reply_text(
            f"✅ Información de {nombre}:\n"
            f"- Código: {codigo}\n- Zona: {zona}\n- Jefe: {jefe}"
        )
    except:
        await update.message.reply_text("Opción inválida.")
    await update.message.reply_text(
        "¿Desea hacer otra consulta?\n"
        "1) Buscar por nombre\n"
        "2) Buscar por código\n"
        "3) Buscar por zona\n"
        "4) No, ya terminé"
    )
    return ELEGIR

# Cancelar
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Consulta cancelada.")
    return ConversationHandler.END

# Crear app

import os
app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()


# Conversación
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ELEGIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, elegir)],
        BUSCAR_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, buscar_nombre)],
        BUSCAR_CODIGO: [MessageHandler(filters.TEXT & ~filters.COMMAND, buscar_codigo)],
        BUSCAR_ZONA: [MessageHandler(filters.TEXT & ~filters.COMMAND, buscar_zona)],
        ELEGIR_UNIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, elegir_unidad)],
    },
    fallbacks=[CommandHandler("cancelar", cancelar)],
)

app.add_handler(conv_handler)
app.run_polling()