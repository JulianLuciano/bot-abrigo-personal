import requests
import os
import utils as ut
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

# Estados de la conversación
ASK_HOURS, ASK_COORDINATES, ASK_RAIN, RESPOND_RAIN = range(4)

TOKEN = os.environ["TOKEN"]
API_URL = os.environ.get("API_URL")
VIDEO_HELP_ID = "BAACAgEAAxkBAAIDlWg-WReZDKCtaoSzifGdWYoMjiKxAALNBQACtDn4RZHLQHkH-6GqNgQ" 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 ¡Bienvenido al bot de recomendación de abrigo! 🌡️\n\n"
        "Estas son las funciones disponibles:\n\n"
        "/abrigo - Recomendación de abrigo actual\n"
        "/abrigo_2h - Recomendación para dentro de 2 horas\n"
        "/abrigo_3h - Recomendación para dentro de 3 horas\n"
        "/abrigo_4h - Recomendación para dentro de 4 horas\n"
        "/abrigo_nhs - Recomendación para N horas adelante (hasta 48hs)\n"
        "/help - Guía de uso del bot\n\n"
        "¡Enviá /abrigo para comenzar!"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🎥 *Guía de uso del bot*\n\n"
        "1\. Usá uno de estos comandos:\n"
        "   /abrigo \- Recomendación actual\n"
        "   /abrigo\_2h \- Para dentro de 2 horas\n"
        "   /abrigo\_3h \- Para dentro de 3 horas\n"
        "   /abrigo\_4h \- Para dentro de 4 horas\n"
        "   /abrigo\_nhs \- Para N horas adelante \(hasta 48\)\n\n"
        "2\. Enviá coordenadas en formato `latitud,longitud`\n"
        "3\. Recibirás recomendaciones de abrigo\n"
        "4\. Podés consultar la probabilidad de lluvia\n\n"
        "*Ejemplo válido:* `\-34\.58543,\-58\.42567`\n\n"
        "Usá el comando /start para ver todas las opciones"
    )
    
    try:
        await update.message.reply_video(
            video=VIDEO_HELP_ID,
            caption=help_text,
            parse_mode="MarkdownV2",
            supports_streaming=True,
            width=360,
            height=640,
            write_timeout=20
        )
    except Exception as e:
        print(f"Error al enviar video: {str(e)}")
        try:
            await update.message.reply_text(
                help_text,
                parse_mode="MarkdownV2"
            )
        except Exception as e2:
            print(f"Error al enviar texto con formato: {str(e2)}")
            await update.message.reply_text(
                "📌 Cómo usar el bot:\n\n" +
                help_text.replace("\\", "").replace("*", "").replace("`", ""),
                parse_mode=None
            )

async def ask_for_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ingresá la cantidad de horas hacia adelante para las cuales querés el pronóstico (máximo 48hs)")
    return ASK_HOURS

async def handle_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hours = int(update.message.text.strip())
        if hours < 1 or hours > 48:
            await update.message.reply_text("⚠️ Por favor ingresá un número entero entre 1 y 48")
            return ASK_HOURS
            
        context.user_data['hours_ahead'] = hours
        return await ask_for_coordinates(update, context)
        
    except ValueError:
        await update.message.reply_text("⚠️ Por favor ingresá un número entero entre 1 y 48")
        return ASK_HOURS

async def ask_for_coordinates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Por favor, enviá la latitud y longitud de tu ubicación separadas por coma (ej: -34.58,-58.42)")
    return ASK_COORDINATES

async def handle_coordinates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        
        # Diccionario de atajos secretos (se aceptan variantes de mayúsculas y tildes)
        location_shortcuts = {
            'cordoba': (-31.4580911, -64.2199552),
            'córdoba': (-31.4580911, -64.2199552),
            'cba': (-31.4580911, -64.2199552),
            'casa': (-34.5821438, -58.4303663),
            'baires': (-34.5821438, -58.4303663),
            'caba': (-34.5821438, -58.4303663),
            'buenos aires': (-34.5821438, -58.4303663),
            'bs as': (-34.5821438, -58.4303663),
            'capital federal': (-34.5821438, -58.4303663),
        }
        
        # Verificar si el texto es un atajo (ignorando mayúsculas/tildes/espacios)
        lower_text = text.lower().replace(" ", "")
        normalized_text = lower_text.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        
        # Buscar coincidencia en los atajos
        lat, lon = None, None
        for shortcut, coords in location_shortcuts.items():
            if normalized_text == shortcut.lower().replace(" ", ""):
                lat, lon = coords
                break
        
        # Si no es un atajo, procesar como coordenadas normales
        if lat is None or lon is None:
            cleaned_text = text.replace("(", "").replace(")", "").replace(" ", "")
            parts = cleaned_text.split(",")
            
            if (len(parts) != 2 or 
                not all(part.replace(".", "").lstrip("-").isdigit() for part in parts) or 
                cleaned_text.count(".") > 2):
                await update.message.reply_text("⚠️ Formato incorrecto. Usá: lat,lon \nEjemplo: -34.58,-58.42")
                return ASK_COORDINATES
                
            lat, lon = map(float, parts)
        hours_ahead = context.user_data.get('hours_ahead', 0)

        payload = {"lat": lat, "lon": lon, 'lead': hours_ahead}
        
        r = requests.post(API_URL, json=payload)
        if r.status_code == 200:
            data = r.json()
            class_1st = data["class_1st"]
            prob_1st = round(data["prob_1st"] * 100)
            class_2nd = data["class_2nd"]
            prob_2nd = round(data["prob_2nd"] * 100)
            temperature = data['temperature']
            humidity = data['humidity']
            wind = data['weather_wind_speed_10m'] * 3.6
            apparent_temperature = data['apparent_temperature']
            emoji = ut.temperatura_emoji(apparent_temperature)
            abrigo_1 = ut.abrigo_emoji(class_1st)
            abrigo_2 = ut.abrigo_emoji(class_2nd)
            hour_geo = data["hour_geo"]
            verbo = 'será' if (data['minute'] >= 30 or hours_ahead > 0) else 'es'
            precipitation_prob = round(data['precipitation_prob'] * 100, 1)
            context.user_data['precipitation_prob'] = precipitation_prob
            precipitation = data['precipitation']
            context.user_data['precipitation'] = precipitation

            time_prefix = ""
            if hours_ahead > 0:
                time_prefix = f"dentro de {hours_ahead} horas, "
            
            msg = (
                f"📍 En tu ubicación, {time_prefix}a las {hour_geo} hs, la temperatura {verbo} de {temperature:.1f}° con una humedad de {humidity:.0f}% y viento a {wind:.1f} km/h, "
                f"provocando una *sensación térmica de {apparent_temperature:.1f}°* {emoji}\n\n"
                f"Te recomiendo usar: {abrigo_1} {class_1st} ({prob_1st}% prob)"
            )
            
            if data["prob_1st"] <= 0.6 and (data["prob_2nd"] > 0.25 or (data["prob_1st"] - data["prob_2nd"] < 0.10)):
                msg += f"\nSi no, podrías usar: {abrigo_2} {class_2nd} ({prob_2nd}% prob)"
            
            await update.message.reply_text(msg, parse_mode="Markdown")
            
            reply_keyboard = [['Sí', 'No']]
            await update.message.reply_text(
                "¿Querés saber si va a llover?",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, 
                    one_time_keyboard=True,
                    input_field_placeholder='Sí o No?'
                )
            )
            return ASK_RAIN
            
        else:
            await update.message.reply_text("⚠️ Error al consultar la predicción.")
            return ConversationHandler.END
            
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("❗ Por favor mandá coordenadas como: -34.58,-58.42. \nAntes, volvé a iniciarme con /start")
        return ConversationHandler.END

async def handle_rain_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_response = update.message.text.lower()
    
    if user_response in ['sí', 'si', 's']:
        await update.message.reply_text(
            f"La probabilidad de lluvia es del {context.user_data['precipitation_prob']}%. " + 
            f"{ut.lluvia_msj(context.user_data['precipitation_prob'], context.user_data['precipitation'])}.",
            reply_markup=None
        )
    
    if 'hours_ahead' in context.user_data:
        del context.user_data['hours_ahead']
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'hours_ahead' in context.user_data:
        del context.user_data['hours_ahead']
    
    await update.message.reply_text(
        "Consulta cancelada",
        reply_markup=None
    )
    return ConversationHandler.END

async def abrigo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hours_ahead'] = 0
    return await ask_for_coordinates(update, context)

async def abrigo_2h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hours_ahead'] = 2
    return await ask_for_coordinates(update, context)

async def abrigo_3h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hours_ahead'] = 3
    return await ask_for_coordinates(update, context)

async def abrigo_4h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hours_ahead'] = 4
    return await ask_for_coordinates(update, context)

async def abrigo_nhs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await ask_for_hours(update, context)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handler para abrigo_nhs
    nhs_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("abrigo_nhs", abrigo_nhs)],
        states={
            ASK_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hours)],
            ASK_COORDINATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_coordinates)],
            ASK_RAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rain_response)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    # Handler para los otros comandos de abrigo
    abrigo_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("abrigo", abrigo),
            CommandHandler("abrigo_2h", abrigo_2h),
            CommandHandler("abrigo_3h", abrigo_3h),
            CommandHandler("abrigo_4h", abrigo_4h)
        ],
        states={
            ASK_COORDINATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_coordinates)],
            ASK_RAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rain_response)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(nhs_conversation_handler)
    app.add_handler(abrigo_conversation_handler)
    
    app.run_polling()

if __name__ == '__main__':
    main()