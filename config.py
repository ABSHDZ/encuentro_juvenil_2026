import os
import string
import random

# --- CONFIGURACIÓN DE LA APLICACIÓN ---
class Config:
    # Clave secreta (importante para sesiones y seguridad)
    SECRET_KEY = "b7190a1e837611c89c6711ddd1ba347950e718ea8d8d9cc45b86e5371f8ff094"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///event_management.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_recycle' : 280}

# --- CONSTANTES Y MOCK DATA ---

OPCIONES_PROCEDENCIA = [
    "Aguascalientes",
    "Baja California",
    "Baja California Sur",
    "Campeche",
    "Chiapas",
    "Chihuahua",
    "Ciudad de México",
    "Coahuila",
    "Colima",
    "Durango",
    "Estado de México",
    "Guanajuato",
    "Guerrero",
    "Hidalgo",
    "Jalisco",
    "Michoacán",
    "Morelos",
    "Nayarit",
    "Nuevo León",
    "Oaxaca",
    "Puebla",
    "Querétaro",
    "Quintana Roo",
    "San Luis Potosí",
    "Sinaloa",
    "Sonora",
    "Tabasco",
    "Tamaulipas",
    "Tlaxcala",
    "Veracruz",
    "Yucatán",
    "Zacatecas",
    "Otro...",
    ]

OPCIONES_TRANSPORTE = ["Avión", "Autobús", "Coche", "Camión", "Otro"]
OPCIONES_MEMBRESIA = ["Miembro", "Visitante"]
OPCIONES_SITUACION = ["Bautizado", "No bautizado"]
OPCIONES_HOSPEDAJE = ["Sí", "No"]
MONTO_PAGO = 200.00
CONCEPTO_BASE = "QR ASISTENCIA"

# --- NUEVOS DATOS DE CUENTA BANCARIA ---
BANK_ACCOUNTS = [
    {
        "bank_name": "Banorte",
        "clabe": "000000000000000001",
        "card_number": "0000000000001010",
        "owner": "Sujeto A",
        "style_class": "bg-red-600"
    },
    {
        "bank_name": "BBVA",
        "clabe": "000000000000000002",
        "card_number": "0000000000002020",
        "owner": "Sujeto B",
        "style_class": "bg-blue-800"
    }
]

# --- NUEVOS ESTADOS DE PAGO ---
PAYMENT_STATUS = {
    "NO_PAID": "Sin Pago Realizado",
    "PENDING": "Pendiente de Revisión",
    "CONFIRMED": "Pago Confirmado",
    "REJECTED": "Rechazado"
}

def generate_group_code(length=6):
    """Genera un código alfanumérico aleatorio para el grupo."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for i in range(length))

# Exportamos las opciones para fácil acceso
APP_OPTIONS = {
    "procedencia": OPCIONES_PROCEDENCIA,
    "transporte": OPCIONES_TRANSPORTE,
    "membresia": OPCIONES_MEMBRESIA,
    "situacion": OPCIONES_SITUACION,
    "hospedaje": OPCIONES_HOSPEDAJE,
    "monto": MONTO_PAGO,
    "concepto": CONCEPTO_BASE,
    "payment_status": PAYMENT_STATUS,
    "bank_accounts": BANK_ACCOUNTS # Exportar las cuentas
}