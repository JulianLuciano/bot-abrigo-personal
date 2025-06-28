def temperatura_emoji(apparent_temperature):
    if apparent_temperature > 30:
        return '🥵'
    elif 25 < apparent_temperature <= 30:
        return '☀️☀️'
    elif 16 < apparent_temperature <= 25:
        return '☀️'
    elif 11 < apparent_temperature <= 16:
        return '🌤️'
    elif 6.5 < apparent_temperature <= 11:
        return '☁️☁️'
    else:
        return '🥶'

def abrigo_emoji(clase):
    if clase == "en cuero":
        return '🤽🏻‍♂️'
    elif clase == "remera":
        return '👕'
    elif clase == "rompevientos":
        return '🌬️🧥'
    elif clase == "sweater":
        return '👕👕'
    elif clase == "campera":
        return '🧥'
    elif clase == "buzo":
        return '🧥'
    elif clase == "buzo/hoodie":
        return '🧥'
    elif clase == "camperon":
        return '🧥🧥'
    elif clase == "camperon y buzo":
        return '🧥🧥🧣'
    elif clase == "camperon buzo y termica":
        return '🧥🧤🧣'
    
def lluvia_msj(prob,intensidad):
    if intensidad >= 2:
        return 'Salir con ☔️ es imprenscindible hoy, hay lluvia intensa' 
    elif prob < 30:
        return 'Salir con ☔️ no es necesario hoy' 
    elif prob >= 30 and prob <50:
        return 'Salir con ☔️ es opcional hoy' 
    elif prob >= 50 and prob <70:
        return 'Salir con ☔️ es recomendable hoy' 
    elif prob >= 70:
        return 'Salir con ☔️ es imprenscindible hoy' 