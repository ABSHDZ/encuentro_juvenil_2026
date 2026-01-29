from flask_sqlalchemy import SQLAlchemy
from config import APP_OPTIONS

# Inicializamos el objeto SQLAlchemy. La inicialización final se hace en app.py
db = SQLAlchemy()

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False) # El código es el nombre del grupo
    # Relación uno-a-muchos con User (Group tiene muchos Users)
    users = db.relationship('User', backref='group', lazy=True)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    # Campos Editables y Requeridos
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.BigInteger, nullable=False)
    city = db.Column(db.String(100), nullable=False) # Procedencia
    needs_lodging = db.Column(db.String(5), nullable=False) # ¿Necesitas Hospedaje? (Sí/No)
    transport = db.Column(db.String(100), nullable=False) # ¿Cómo planeas llegar?
    local_name = db.Column(db.String(100), nullable=False) # Nombre del Local
    membership = db.Column(db.String(50), nullable=False) # Membresía
    situation = db.Column(db.String(50), nullable=False) # Situación
    # NUEVO CAMPO: Estado de Pago
    payment_status = db.Column(db.String(50),
                               default=APP_OPTIONS["payment_status"]["NO_PAID"],
                               nullable=False)
    # Relación con Group
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    #Administrador
    is_special = db.Column(db.Boolean, default=False) # Usuario Especial/Administrador
    attendance_registered = db.Column(db.Boolean, default=False) # Registro de Asistencia
    is_group_responsible = db.Column(db.Boolean, default=False) # Responsable de Grupo

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Datos de la transferencia
    amount = db.Column(db.Float, nullable=False)
    reference = db.Column(db.String(100), nullable=False)
    concept = db.Column(db.String(100), nullable=False)
    bank_issuer = db.Column(db.String(100), nullable=False)
    bank_receiver = db.Column(db.String(100), nullable=False)
    transaction_date = db.Column(db.String(20), nullable=False) # Guardamos como string para simplicidad
    status = db.Column(db.String(20), default='Pendiente') # Pendiente, Revisado, Error

# Importa los modelos para que puedan ser usados por otras rutas
__all__ = ['db', 'Group', 'User', 'Payment']