import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

COMUNIDADES = [
    {
        "id_comunidad": -1002983018006,
        "temas": {
            "theme_Anuncios": 207,
            "theme_questions": 7,
            "theme_escuela": 6,
            "theme_juegosYcasino": 16785,
            "theme_NSFW": 5,
            "theme_Exhibicionismo": 4,
            "theme_libreria": 3,
            "theme_multimedia": 15,
            "theme_platica": 28175,
            "theme_test": 43,
            "theme_reglas": 8,
            "theme_presentaciones": 2,
            "theme_rincon": 36205
        }
    }
]

ADMINS = [
    {
        "id_comunidad": -1002983018006,
        "admins": {
            1174798556
        }
    }
]

DOMS = {
    1174798556: []
}

PUNISHMENT_FILE = "punishments.json"

def obtener_temas_por_comunidad(community_id: int):
    for comunidad in COMUNIDADES:
        if comunidad["id_comunidad"] == community_id:
            return comunidad["temas"]
    return None