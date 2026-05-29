import os
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, render_template, redirect, url_for,
    session, request, jsonify
)
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from supabase import create_client, Client

# ── Config ─────────────────────────────────────────────────────────────────────
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']
app.config['SESSION_COOKIE_SECURE'] = False   # True en producción (HTTPS)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ── Auth0 ──────────────────────────────────────────────────────────────────────
AUTH0_DOMAIN = os.environ['AUTH0_DOMAIN']

oauth = OAuth(app)
auth0 = oauth.register(
    'auth0',
    client_id=os.environ['AUTH0_CLIENT_ID'],
    client_secret=os.environ['AUTH0_CLIENT_SECRET'],
    client_kwargs={'scope': 'openid profile email'},
    server_metadata_url=f'https://{AUTH0_DOMAIN}/.well-known/openid-configuration',
)

# ── Supabase ───────────────────────────────────────────────────────────────────
supabase: Client = create_client(
    os.environ['SUPABASE_URL'],
    os.environ['SUPABASE_SERVICE_KEY'],
)

# ── Helpers ────────────────────────────────────────────────────────────────────
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_user(role: str, auth0_id: str, email: str, nombre: str) -> None:
    """Crea o actualiza el usuario en la tabla de Supabase correspondiente."""
    table = 'administradores' if role == 'admin' else 'vecinos'
    supabase.table(table).upsert(
        {'auth0_id': auth0_id, 'email': email, 'nombre': nombre, 'last_login': now_iso()},
        on_conflict='auth0_id'
    ).execute()


def get_user_profile(role: str, auth0_id: str):
    """Obtiene el perfil del usuario desde Supabase."""
    table = 'administradores' if role == 'admin' else 'vecinos'
    result = supabase.table(table).select('*').eq('auth0_id', auth0_id).single().execute()
    return result.data


# ── Auth decorator ─────────────────────────────────────────────────────────────
def require_auth(allowed_roles=None):
    """Decorador que verifica sesión activa. Opcionalmente restringe por rol."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = session.get('user')
            if not user:
                return redirect(url_for('login'))
            if allowed_roles and user.get('role') not in allowed_roles:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── Páginas públicas ───────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    # Si ya está logueado, redirigir al dashboard
    user = session.get('user')
    if user:
        return redirect(url_for('dashboard', role=user['role']))
    return render_template('login.html')


# ── Auth0 flow ─────────────────────────────────────────────────────────────────
@app.route('/auth/login')
def auth_login():
    """Inicia el flujo OAuth2 hacia Auth0. El rol se guarda en sesión."""
    role = request.args.get('role', 'vecino')
    if role not in ('admin', 'vecino'):
        role = 'vecino'

    session['pending_role'] = role
    callback_url = url_for('auth_callback', _external=True)
    return auth0.authorize_redirect(redirect_uri=callback_url)


@app.route('/auth/callback')
def auth_callback():
    """Auth0 redirige aquí después del login con el código de autorización."""
    token = auth0.authorize_access_token()
    userinfo = token.get('userinfo', {})

    auth0_id = userinfo.get('sub')
    email    = userinfo.get('email', '')
    nombre   = userinfo.get('name', email)
    role     = session.pop('pending_role', 'vecino')

    # Guardar/actualizar en Supabase
    upsert_user(role, auth0_id, email, nombre)

    # Guardar sesión en Flask
    session['user'] = {
        'sub':   auth0_id,
        'email': email,
        'name':  nombre,
        'role':  role,
    }

    return redirect(url_for('dashboard', role=role))


@app.route('/auth/logout')
def auth_logout():
    """Cierra sesión en Flask y en Auth0."""
    session.clear()
    return redirect(
        f'https://{AUTH0_DOMAIN}/v2/logout'
        f'?returnTo={url_for("index", _external=True)}'
        f'&client_id={os.environ["AUTH0_CLIENT_ID"]}'
    )


# ── Dashboards protegidos ──────────────────────────────────────────────────────
@app.route('/dashboard/<role>')
@require_auth()
def dashboard(role):
    user = session['user']

    # El rol de la sesión tiene que coincidir con la URL
    if user['role'] != role:
        return redirect(url_for('dashboard', role=user['role']))

    if role == 'admin':
        return render_template('admin_dashboard.html', user=user)
    elif role == 'vecino':
        return render_template('vecino_dashboard.html', user=user)
    else:
        return redirect(url_for('login'))


# ── API: perfil del usuario actual ────────────────────────────────────────────
@app.route('/api/me')
@require_auth()
def api_me():
    user = session['user']
    profile = get_user_profile(user['role'], user['sub'])
    return jsonify(profile)


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('🏢 Niddo server starting...')
    print('📍 http://localhost:3500')
    app.run(host='127.0.0.1', port=3500, debug=True)
