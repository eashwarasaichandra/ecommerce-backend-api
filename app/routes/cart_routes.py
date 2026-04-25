from flask import Blueprint, request, jsonify
from app.models import CartItem, Product
from app import db
from app.utils import token_required

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/', methods=['GET'])
@token_required
def get_cart(current_user):
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    result = []
    total = 0
    
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product:
            item_total = product.price * item.quantity
            total += item_total
            result.append({
                'id': item.id,
                'product_id': product.id,
                'product_name': product.name,
                'price': product.price,
                'quantity': item.quantity,
                'item_total': item_total,
                'image_url': product.image_url
            })
            
    return jsonify({
        'items': result,
        'cart_total': total
    }), 200

@cart_bp.route('/add', methods=['POST'])
@token_required
def add_to_cart(current_user):
    data = request.get_json()
    if not data or not data.get('product_id'):
        return jsonify({'message': 'Missing product_id'}), 400
        
    product_id = data['product_id']
    quantity = data.get('quantity', 1)
    
    # Check if product exists and has stock
    product = Product.query.get_or_404(product_id)
    if product.stock < quantity:
        return jsonify({'message': 'Not enough stock available'}), 400
        
    # Check if item already in cart
    existing_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if existing_item:
        existing_item.quantity += quantity
    else:
        new_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(new_item)
        
    db.session.commit()
    return jsonify({'message': 'Item added to cart successfully!'}), 200
    
@cart_bp.route('/remove/<int:item_id>', methods=['DELETE'])
@token_required
def remove_from_cart(current_user, item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item removed from cart'}), 200
