from functools import wraps
from flask import session, redirect, url_for
from models import db, User

def login_required(f):
    """Decorador simple para asegurar que un usuario ha iniciado sesión."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # flash('Debes iniciar sesión para acceder a esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Obtiene el objeto User de la sesión."""
    if 'user_id' in session:
        # Usa db.session.get para obtener el objeto User por ID.
        # Asume que el contexto de la aplicación está activo (lo estará en las rutas)
        return db.session.get(User, session['user_id'])
    return None