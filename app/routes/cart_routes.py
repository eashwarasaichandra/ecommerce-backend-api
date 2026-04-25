from flask import Blueprint, request, jsonify
from app.models import CartItem, Product
from app import db
from app.utils import token_required

cart_bp = Blueprint('cart', __name__)


# -----------------------------------------------------------------------
# GET /api/cart/  — view current user's cart
# -----------------------------------------------------------------------
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
                'item_total': round(item_total, 2),
                'image_url': product.image_url,
                'stock_available': product.stock
            })

    return jsonify({
        'items': result,
        'cart_total': round(total, 2),
        'item_count': len(result)
    }), 200


# -----------------------------------------------------------------------
# POST /api/cart/add  — add item (or increment quantity) in cart
# -----------------------------------------------------------------------
@cart_bp.route('/add', methods=['POST'])
@token_required
def add_to_cart(current_user):
    data = request.get_json()
    if not data or not data.get('product_id'):
        return jsonify({'message': 'Missing product_id'}), 400

    product_id = data['product_id']
    quantity = int(data.get('quantity', 1))

    if quantity < 1:
        return jsonify({'message': 'Quantity must be at least 1'}), 400

    product = Product.query.get_or_404(product_id)

    existing_item = CartItem.query.filter_by(
        user_id=current_user.id, product_id=product_id
    ).first()

    new_total_qty = (existing_item.quantity + quantity) if existing_item else quantity

    if product.stock < new_total_qty:
        return jsonify({
            'message': f'Not enough stock. Available: {product.stock}, Requested total: {new_total_qty}'
        }), 400

    if existing_item:
        existing_item.quantity = new_total_qty
    else:
        db.session.add(CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity))

    db.session.commit()
    return jsonify({
        'message': 'Item added to cart successfully!',
        'product': product.name,
        'quantity_in_cart': new_total_qty
    }), 200


# -----------------------------------------------------------------------
# PUT /api/cart/update/<item_id>  — update quantity of a specific cart item
# -----------------------------------------------------------------------
@cart_bp.route('/update/<int:item_id>', methods=['PUT'])
@token_required
def update_cart_item(current_user, item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    data = request.get_json()

    if not data or 'quantity' not in data:
        return jsonify({'message': 'Missing "quantity" field'}), 400

    quantity = int(data['quantity'])

    if quantity < 1:
        return jsonify({'message': 'Quantity must be at least 1. Use DELETE to remove the item.'}), 400

    product = Product.query.get(item.product_id)
    if product and product.stock < quantity:
        return jsonify({
            'message': f'Not enough stock. Available: {product.stock}'
        }), 400

    item.quantity = quantity
    db.session.commit()
    return jsonify({
        'message': 'Cart item updated.',
        'item_id': item_id,
        'new_quantity': quantity,
        'new_item_total': round(product.price * quantity, 2) if product else None
    }), 200


# -----------------------------------------------------------------------
# DELETE /api/cart/remove/<item_id>  — remove item from cart
# -----------------------------------------------------------------------
@cart_bp.route('/remove/<int:item_id>', methods=['DELETE'])
@token_required
def remove_from_cart(current_user, item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item removed from cart.'}), 200


# -----------------------------------------------------------------------
# DELETE /api/cart/clear  — empty entire cart
# -----------------------------------------------------------------------
@cart_bp.route('/clear', methods=['DELETE'])
@token_required
def clear_cart(current_user):
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'message': 'Cart cleared.'}), 200
