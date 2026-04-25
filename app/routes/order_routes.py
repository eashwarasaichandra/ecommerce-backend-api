from flask import Blueprint, request, jsonify
from app.models import CartItem, Product, Order, OrderItem
from app import db
from app.utils import token_required

order_bp = Blueprint('orders', __name__)

@order_bp.route('/', methods=['GET'])
@token_required
def get_orders(current_user):
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    result = []
    
    for order in orders:
        items = []
        for item in order.items:
            items.append({
                'product_id': item.product_id,
                'product_name': item.product.name if item.product else 'Unknown Product',
                'quantity': item.quantity,
                'price_at_purchase': item.price_at_purchase
            })
            
        result.append({
            'id': order.id,
            'total_price': order.total_price,
            'status': order.status,
            'payment_status': getattr(order, 'payment_status', 'N/A'),
            'created_at': order.created_at.isoformat(),
            'items': items
        })
        
    return jsonify(result), 200

@order_bp.route('/', methods=['POST'])
@token_required
def create_order(current_user):
    # Get all cart items for user
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        return jsonify({'message': 'Cart is empty'}), 400
        
    total_price = 0
    order_items_to_create = []
    
    # Calculate total and verify stock
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if not product or product.stock < item.quantity:
            return jsonify({'message': f'Not enough stock for product ID {item.product_id}'}), 400
            
        item_total = product.price * item.quantity
        total_price += item_total
        
        # Decrease stock
        product.stock -= item.quantity
        
        # Prepare order item
        order_items_to_create.append({
            'product_id': product.id,
            'quantity': item.quantity,
            'price_at_purchase': product.price
        })
        
    import time
    import random
    
    # Create order first in 'processing' state
    new_order = Order(user_id=current_user.id, total_price=total_price, status='pending', payment_status='processing')
    db.session.add(new_order)
    db.session.flush() # To get the new_order.id
    
    # Create order items
    for oi in order_items_to_create:
        new_order_item = OrderItem(
            order_id=new_order.id,
            product_id=oi['product_id'],
            quantity=oi['quantity'],
            price_at_purchase=oi['price_at_purchase']
        )
        db.session.add(new_order_item)
        
    db.session.commit() # Save the processing order
    
    # ---------------------------------------------
    # SIMULATE PAYMENT GATEWAY MICROSERVICE (Stripe)
    # ---------------------------------------------
    time.sleep(2) # simulate network latency
    payment_success = random.random() > 0.10 # 90% success rate
    
    if not payment_success:
        # Revert stock since payment failed
        for item in cart_items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity
        
        new_order.payment_status = 'failed'
        new_order.status = 'cancelled'
        db.session.commit()
        return jsonify({'message': 'Payment failed. Please try a different card.', 'order_id': new_order.id}), 402
        
    # Payment succeeded
    new_order.payment_status = 'paid'
    new_order.status = 'completed'
    
    # Clear cart only on success
    for item in cart_items:
        db.session.delete(item)
        
    db.session.commit()
    
    return jsonify({
        'message': 'Payment successful! Order placed.',
        'order_id': new_order.id,
        'total_price': total_price
    }), 201
