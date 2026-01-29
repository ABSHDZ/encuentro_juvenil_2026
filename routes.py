from flask import render_template, request, redirect, url_for, session, flash, current_app, Response
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Group, Payment
from config import APP_OPTIONS, generate_group_code
from utils import login_required, get_current_user
import qrcode
import io
import base64
from qrcode.image.svg import SvgImage

# --- RUTAS DE LA APLICACIÓN ---

def init_routes(app):
    """Inicializa todas las rutas de la aplicación en el objeto Flask."""

    @app.route('/')
    def index():
        user = get_current_user()
        return render_template('index.html', title="Encuentro Juvenil 2026", current_user=user)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if get_current_user():
            return redirect(url_for('index'))

        if request.method == 'POST':
            email = request.form.get('email', '').lower()
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            # Validación
            if password != confirm_password:
                flash('Las contraseñas no coinciden.', 'error')
                return redirect(url_for('register'))

            if db.session.execute(db.select(User).filter_by(email=email)).scalar():
                flash('El email ya está registrado.', 'error')
                return redirect(url_for('register'))

            try:
                # Recuperar otros datos del formulario
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

                new_user = User(
                    email=email,
                    password_hash=hashed_password,
                    name=request.form['name'],
                    age=int(request.form['age']),
                    phone=int(request.form['phone']),
                    city=request.form['city'],
                    needs_lodging=request.form['needs_lodging'],
                    transport=request.form['transport'],
                    local_name=request.form['local_name'],
                    membership=request.form['membership'],
                    situation=request.form['situation'],
                    payment_status=APP_OPTIONS["payment_status"]["NO_PAID"], # Estado de pago inicial
                    group_id=None
                )

                db.session.add(new_user)
                db.session.commit()
                session['user_id'] = new_user.id
                flash('Registro exitoso. ¡Bienvenido!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error en el registro: {e}', 'error')
                current_app.logger.error(f"Error de DB al registrar: {e}")
                return redirect(url_for('register'))

        return render_template('auth/register.html', title="Registro de Usuario", **APP_OPTIONS)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if get_current_user():
            return redirect(url_for('index'))

        if request.method == 'POST':
            email = request.form.get('email', '').lower()
            current_password = request.form.get('current_password')
            user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
            if user and check_password_hash(user.password_hash, current_password):
                session['user_id'] = user.id
                flash('Inicio de sesión exitoso.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Email o contraseña incorrectos.', 'error')

        return render_template('auth/login.html', title="Iniciar Sesión")

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('Has cerrado sesión.', 'info')
        return redirect(url_for('index'))

    @app.route('/profile')
    @login_required
    def profile():
        user = get_current_user()
        # El acceso a 'user.group' funciona gracias al 'backref' en el modelo
        return render_template('user/profile.html', title=f"Perfil de {user.name}", current_user=user, payment_statuses=APP_OPTIONS["payment_status"])

    @app.route('/edit_profile', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        user = get_current_user()

        if request.method == 'POST':
            try:
                user.name = request.form['name']
                user.age = int(request.form['age'])
                user.phone = int(request.form['phone'])
                user.city = request.form['city']
                user.needs_lodging = request.form['needs_lodging']
                user.transport = request.form['transport']
                user.local_name = request.form['local_name']
                user.membership = request.form['membership']
                user.situation = request.form['situation']

                db.session.commit()
                flash('Perfil actualizado exitosamente.', 'success')
                return redirect(url_for('profile'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error al actualizar el perfil: {e}', 'error')
                current_app.logger.error(f"Error de DB al editar: {e}")
                return redirect(url_for('edit_profile'))

        return render_template('user/edit_profile.html', title="Editar Perfil", user=user, **APP_OPTIONS)

    @app.route('/group_management')
    @login_required
    def group_management():
        user = get_current_user()
        group = user.group if user.group_id else None
        members = []

        if group:
            members_query = db.select(User).filter_by(group_id=group.id).order_by(User.name)
            members = db.session.execute(members_query).scalars().all()

        return render_template('user/group_management.html', title="Gestión de Hospedaje en Grupos", current_user=user, group=group, members=members)


    @app.route('/create_group', methods=['POST'])
    @login_required
    def create_group():
        user = get_current_user()

        if user.group_id is not None:
            flash('Ya perteneces a un grupo.', 'error')
            return redirect(url_for('group_management'))

        # Generar un código único
        while True:
            code = generate_group_code()
            if not db.session.execute(db.select(Group).filter_by(code=code)).scalar():
                break

        new_group = Group(code=code)
        db.session.add(new_group)
        db.session.flush() # Obtener el ID antes de commit

        user.group_id = new_group.id
        user.is_group_responsible = True

        try:
            db.session.commit()
            flash(f'Grupo "{code}" creado y te has unido exitosamente.', 'success')
            return redirect(url_for('group_management'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el grupo: {e}', 'error')
            current_app.logger.error(f"Error de DB al crear grupo: {e}")
            return redirect(url_for('group_management'))

    @app.route('/join_group', methods=['POST'])
    @login_required
    def join_group():
        user = get_current_user()
        code = request.form.get('code', '').strip().upper()

        if user.group_id is not None:
            flash('Ya perteneces a un grupo.', 'error')
            return redirect(url_for('group_management'))

        group = db.session.execute(db.select(Group).filter_by(code=code)).scalar()

        if not group:
            flash('Código de grupo no encontrado.', 'error')
            return redirect(url_for('group_management'))

        user.group_id = group.id
        user.is_group_responsible = False

        try:
            db.session.commit()
            flash(f'Te has unido al grupo "{group.code}" exitosamente.', 'success')
            return redirect(url_for('group_management'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al unirte al grupo: {e}', 'error')
            current_app.logger.error(f"Error de DB al unirse: {e}")
            return redirect(url_for('group_management'))

    @app.route('/leave_group', methods=['POST'])
    @login_required
    def leave_group():
        user = get_current_user()

        if user.group_id is None:
            flash('No perteneces a ningún grupo.', 'error')
            return redirect(url_for('group_management'))

        group_to_check = user.group # Se mantiene la referencia al grupo

        user.group_id = None
        user.is_group_responsible = False

        try:
            db.session.commit()

            # Opcional: Eliminar el grupo si se queda vacío
            remaining_members = db.session.execute(db.select(User).filter_by(group_id=group_to_check.id)).scalars().all()
            if not remaining_members:
                db.session.delete(group_to_check)
                db.session.commit()
                flash('Has salido del grupo y el grupo vacío ha sido eliminado.', 'info')
            else:
                flash('Has salido del grupo exitosamente.', 'success')

            return redirect(url_for('group_management'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al salir del grupo: {e}', 'error')
            current_app.logger.error(f"Error de DB al salir: {e}")
            return redirect(url_for('group_management'))

    @app.route('/delete_group', methods=['POST'])
    @login_required
    def delete_group():
        user = get_current_user()

        if user.group_id is None:
            flash('No perteneces a ningún grupo.', 'error')
            return redirect(url_for('group_management'))

        if not user.is_group_responsible:
            flash('Solo el responsable del grupo puede eliminarlo.', 'error')
            return redirect(url_for('group_management'))

        group_id_to_delete = user.group_id
        group_to_delete = user.group
        # 1. Eliminar la relación del usuario con el grupo
        try:
            # 2. Liberar a todos los usuarios de ese grupo
            # Usamos update en lugar de cargar todos los objetos en memoria para ser más eficiente
            update_count = db.session.query(User).filter(User.group_id == group_id_to_delete).update(
                {
                    User.group_id: None,
                    User.is_group_responsible: False
                },
                synchronize_session='fetch'
            )
            # 3. Eliminar el objeto Group
            db.session.delete(group_to_delete)
            # 4. Confirmar la transacción
            db.session.commit()
            flash('Has eliminado el grupo exitosamente.', 'success')
            return redirect(url_for('group_management'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar del grupo: {e}', 'error')
            current_app.logger.error(f"Error de DB al eliminar: {e}")
            return redirect(url_for('group_management'))

    # --- RUTAS DE PAGO MANUAL ---

    @app.route('/payment')
    @login_required
    def payment_info():
        user = get_current_user()

        # Pasa la lista de cuentas bancarias
        return render_template('payment/payment_info.html',
            title="Información de Pago",
            current_user=user,
            monto=f'{APP_OPTIONS["monto"]:.2f}',
            concepto=APP_OPTIONS["concepto"],
            bank_accounts=APP_OPTIONS["bank_accounts"] # ¡NUEVO!
        )

    @app.route('/submit_payment', methods=['GET', 'POST'])
    @login_required
    def submit_payment():
        user = get_current_user()

        if request.method == 'POST':
            try:
                # El monto es fijo de la configuración
                amount = request.form["monto"]
                reference = request.form['reference']
                concept = request.form['concept']
                bank_issuer = request.form['bank_issuer']
                transaction_date = request.form['transaction_date']
                bank_receiver_name = request.form['bank_receiver']

                new_payment = Payment(
                    user_id=user.id,
                    amount=amount,
                    reference=reference,
                    concept=concept,
                    bank_issuer=bank_issuer,
                    bank_receiver=bank_receiver_name, # Usamos un valor fijo para el registro
                    transaction_date=transaction_date,
                    status='Pendiente'
                )

                db.session.add(new_payment)

                # Actualizar el estado de pago del usuario
                user.payment_status = APP_OPTIONS["payment_status"]["PENDING"]

                db.session.commit()

                flash('Registro de pago exitoso. Su pago está pendiente de revisión manual.', 'success')
                return redirect(url_for('profile'))

            except ValueError:
                flash('Monto inválido. Asegúrate de que el valor sea numérico.', 'error')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al registrar el pago: {e}', 'error')
                current_app.logger.error(f"Error de DB al registrar pago: {e}")

            # En caso de error, volvemos a mostrar el formulario
            return redirect(url_for('submit_payment'))

        return render_template('payment/submit_payment.html',
            title="Registrar Transferencia",
            current_user=user,
            monto=f'{APP_OPTIONS["monto"]:.2f}',
            concepto=APP_OPTIONS["concepto"],
            bank_accounts=[account["bank_name"] for account in APP_OPTIONS["bank_accounts"]]  # Pasar las cuentas al formulario
        )

    @app.route('/my_qr_code')
    @login_required
    def my_qr_code():
        user = get_current_user()
        status = user.payment_status
        qr_base64 = None

        # Solo generar el QR si el pago está confirmado
        if status == APP_OPTIONS["payment_status"]["CONFIRMED"]:

            # 1. Definir el contenido del QR (puede ser una URL o datos del usuario)
            qr_data = f"https://abshdz.pythonanywhere.com/attendance/{user.id}"

            # 2. Generar el código QR como SVG en memoria
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            # Usar el factory para crear una imagen SVG
            img = qr.make_image(image_factory=SvgImage)

            # Guardar el SVG en un buffer de memoria (IO)
            buffer = io.BytesIO()
            img.save(buffer)
            buffer.seek(0)

            # 3. Codificar en Base64 para incrustar en HTML
            svg_content = buffer.getvalue().decode('utf-8')
            qr_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')

        return render_template('qr_code.html',
            title="Tu Código QR de Asistencia",
            current_user=user,
            status=status,
            confirmed_status=APP_OPTIONS["payment_status"]["CONFIRMED"],
            qr_base64=qr_base64
        )

    @app.route('/attendance/<qr_data>', methods=['GET'])
    @login_required
    def attendance_check(qr_data):
        user = get_current_user()
        # 1. Verificar si el usuario que accede a esta ruta es especial
        if not user.is_special:
            # Si no hay sesión o no es un usuario especial, denegar el acceso
            return render_template('attendance_check.html',
                                message='No Autorizado',
                                detail='No estás autorizado para registrar asistencia.',
                                status='unauthorized',
                                current_user=user)
        # 2. Procesar el contenido del QR para obtener el ID del usuario
        try:
            # El formato es: url/id
            user_to_check = User.query.get_or_404(qr_data)
            if not user_to_check:
                return render_template('attendance_check.html',
                                    message='Error',
                                    detail='Código QR no válido o usuario no encontrado.',
                                    status='error',
                                    current_user=user)
            # 3. Registrar la asistencia
            if user_to_check.attendance_registered:
                message = 'Asistencia YA Registrada'
                detail = f'{user_to_check.name} ya había registrado su asistencia.'
                status = 'already_registered'
            else:
                # Aquí podríamos añadir la verificación de pago, pero el requisito solo pide registro
                if user_to_check.payment_status != 'Pago Confirmado':
                    return render_template('attendance_check.html',
                                    message='Error',
                                    detail='Pago pendiente.',
                                    status='error',
                                    current_user=user)
                user_to_check.attendance_registered = True
                db.session.commit()

                message = 'Asistencia Registrada'
                detail = f'¡Asistencia de {user_to_check.name} registrada con éxito!'
                status = 'success'
            return render_template('attendance_check.html', message=message, detail=detail, status=status, current_user=user)
        except Exception as e:
            db.session.rollback()
            return render_template('attendance_check.html',
                                message='Error del Sistema',
                                detail=f'Ocurrió un error al procesar el QR. {e}',
                                status='system_error',
                                current_user=user)

    @app.route('/news')
    def panfleto():
        user = get_current_user()
        return render_template('panfleto.html', title="Volviendo al Diseño" , current_user=user)

    @app.route('/total_attendance')
    def total_attendance():
        user = get_current_user()
        try:
            total = User.query.filter(User.attendance_registered == True).count()
        except Exception as e:
            total = "Error al obtener el conteo"
        return render_template('totales.html', title="Panel de Control de la Aplicación", total_users=total, current_user=user)