from flask import Blueprint, render_template

ui_bp = Blueprint('ui', __name__)

@ui_bp.route('/')
def index():
    return render_template('products.html')

@ui_bp.route('/login')
def login():
    return render_template('login.html')

@ui_bp.route('/register')
def register():
    return render_template('register.html')

@ui_bp.route('/cart')
def cart():
    return render_template('cart.html')

@ui_bp.route('/orders')
def orders():
    return render_template('orders.html')

@ui_bp.route('/admin')
def admin():
    return render_template('admin.html')
