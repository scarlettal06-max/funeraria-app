from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'solo-desarrollo-cambiar-en-produccion')
app.permanent_session_lifetime = timedelta(minutes=20)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
DB = os.path.join(os.path.dirname(__file__), 'funeraria.db')

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS services(id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL, price TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS contacts(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT, message TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pendiente', created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
    ''')
    if conn.execute('SELECT COUNT(*) c FROM users').fetchone()['c'] == 0:
        conn.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)', ('admin', generate_password_hash('Admin123!'), 'admin'))
        conn.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)', ('empleado', generate_password_hash('Empleado123!'), 'employee'))
    if conn.execute('SELECT COUNT(*) c FROM services').fetchone()['c'] == 0:
        conn.executemany('INSERT INTO services(name,description,price) VALUES(?,?,?)', [
            ('Servicio Esencial','Atención y acompañamiento básico para la familia.','$12,500 MXN'),
            ('Servicio Integral','Sala de velación, traslado local y acompañamiento personalizado.','$22,900 MXN'),
            ('Servicio Cremación','Gestión de cremación y urna con atención profesional.','$16,800 MXN')])
    conn.commit(); conn.close()

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('Inicia sesión para continuar.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped

def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return wrapped

@app.route('/')
def home(): return render_template('home.html')

@app.route('/servicios')
def services():
    conn=db(); rows=conn.execute('SELECT * FROM services').fetchall(); conn.close()
    return render_template('services.html', services=rows)

@app.route('/nosotros')
def about(): return render_template('about.html')

@app.route('/contacto', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip(); phone=request.form.get('phone','').strip(); message=request.form.get('message','').strip()
        if not name or not email or '@' not in email or not message:
            flash('Completa nombre, correo válido y mensaje.', 'danger')
        else:
            conn=db(); conn.execute('INSERT INTO contacts(name,email,phone,message) VALUES(?,?,?,?)',(name,email,phone,message)); conn.commit(); conn.close()
            flash('Tu solicitud fue enviada correctamente.', 'success')
            return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/admin/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username=request.form.get('username','').strip(); password=request.form.get('password','')
        conn=db(); user=conn.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone(); conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session.clear(); session.permanent=True; session['user_id']=user['id']; session['username']=user['username']; session['role']=user['role']
            return redirect(url_for('dashboard'))
        flash('Credenciales incorrectas.', 'danger')
    return render_template('login.html')

@app.route('/admin/logout', methods=['POST'])
def logout():
    session.clear(); flash('Sesión cerrada.', 'success'); return redirect(url_for('login'))

@app.route('/admin')
@login_required
def dashboard():
    conn=db(); sc=conn.execute('SELECT COUNT(*) c FROM services').fetchone()['c']; cc=conn.execute('SELECT COUNT(*) c FROM contacts').fetchone()['c']; pc=conn.execute("SELECT COUNT(*) c FROM contacts WHERE status='Pendiente'").fetchone()['c']; conn.close()
    return render_template('dashboard.html', service_count=sc, contact_count=cc, pending_count=pc)

@app.route('/admin/solicitudes')
@login_required
def admin_contacts():
    conn=db(); rows=conn.execute('SELECT * FROM contacts ORDER BY created_at DESC').fetchall(); conn.close()
    return render_template('admin_contacts.html', contacts=rows)

@app.route('/admin/solicitudes/<int:id>/atendida', methods=['POST'])
@login_required
def mark_contact(id):
    conn=db(); conn.execute("UPDATE contacts SET status='Atendida' WHERE id=?",(id,)); conn.commit(); conn.close(); return redirect(url_for('admin_contacts'))

@app.route('/admin/servicios')
@admin_required
def admin_services():
    conn=db(); rows=conn.execute('SELECT * FROM services').fetchall(); conn.close(); return render_template('admin_services.html', services=rows)

@app.route('/admin/servicios/nuevo', methods=['GET','POST'])
@admin_required
def new_service():
    if request.method == 'POST':
        name=request.form.get('name','').strip(); description=request.form.get('description','').strip(); price=request.form.get('price','').strip()
        if name and description and price:
            conn=db(); conn.execute('INSERT INTO services(name,description,price) VALUES(?,?,?)',(name,description,price)); conn.commit(); conn.close(); return redirect(url_for('admin_services'))
        flash('Todos los campos son obligatorios.', 'danger')
    return render_template('service_form.html', title='Nuevo servicio', service=None)

@app.route('/admin/servicios/<int:id>/editar', methods=['GET','POST'])
@admin_required
def edit_service(id):
    conn=db(); service=conn.execute('SELECT * FROM services WHERE id=?',(id,)).fetchone()
    if not service: conn.close(); abort(404)
    if request.method == 'POST':
        name=request.form.get('name','').strip(); description=request.form.get('description','').strip(); price=request.form.get('price','').strip()
        if name and description and price:
            conn.execute('UPDATE services SET name=?,description=?,price=? WHERE id=?',(name,description,price,id)); conn.commit(); conn.close(); return redirect(url_for('admin_services'))
        flash('Todos los campos son obligatorios.', 'danger')
    conn.close(); return render_template('service_form.html', title='Editar servicio', service=service)

@app.route('/admin/servicios/<int:id>/eliminar', methods=['POST'])
@admin_required
def delete_service(id):
    conn=db(); conn.execute('DELETE FROM services WHERE id=?',(id,)); conn.commit(); conn.close(); return redirect(url_for('admin_services'))

@app.errorhandler(403)
def forbidden(e): return render_template('403.html'),403

if __name__ == '__main__':
    init_db(); app.run(debug=True)
