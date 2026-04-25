from flask import Blueprint, request, jsonify
from app.models import CartItem, Product, Order, OrderItem, User
from app import db
from app.utils import token_required, admin_required, is_valid_status_transition, VALID_ORDER_STATUSES
from sqlalchemy import func

order_bp = Blueprint('orders', __name__)


# -----------------------------------------------------------------------
# GET /api/orders/  — current user's own order history
# -----------------------------------------------------------------------
@order_bp.route('/', methods=['GET'])
@token_required
def get_orders(current_user):
    orders = (
        Order.query
        .filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return jsonify(_serialize_orders(orders)), 200


# -----------------------------------------------------------------------
# GET /api/orders/user/<user_id>  — admin: full order history for any user
# Uses explicit SQL JOIN to prove JOIN knowledge
# -----------------------------------------------------------------------
@order_bp.route('/user/<int:user_id>', methods=['GET'])
@admin_required
def get_user_orders(current_user, user_id):
    target_user = User.query.get_or_404(user_id)

    # Explicit JOIN: Orders ↔ OrderItems ↔ Products ↔ Users
    rows = (
        db.session.query(
            Order.id.label('order_id'),
            Order.total_price,
            Order.status,
            Order.payment_status,
            Order.created_at,
            OrderItem.quantity,
            OrderItem.price_at_purchase,
            Product.name.label('product_name'),
            Product.category,
            User.name.label('user_name'),
            User.email.label('user_email'),
        )
        .join(OrderItem, Order.id == OrderItem.order_id)
        .join(Product, OrderItem.product_id == Product.id)
        .join(User, Order.user_id == User.id)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    # Group rows by order_id
    orders_map = {}
    for row in rows:
        if row.order_id not in orders_map:
            orders_map[row.order_id] = {
                'order_id': row.order_id,
                'user_name': row.user_name,
                'user_email': row.user_email,
                'total_price': row.total_price,
                'status': row.status,
                'payment_status': row.payment_status,
                'created_at': row.created_at.isoformat(),
                'items': []
            }
        orders_map[row.order_id]['items'].append({
            'product_name': row.product_name,
            'category': row.category,
            'quantity': row.quantity,
            'price_at_purchase': row.price_at_purchase,
            'item_total': round(row.quantity * row.price_at_purchase, 2)
        })

    return jsonify({
        'user': {'id': target_user.id, 'name': target_user.name, 'email': target_user.email},
        'orders': list(orders_map.values())
    }), 200


# -----------------------------------------------------------------------
# GET /api/orders/all  — admin: all orders across all users
# -----------------------------------------------------------------------
@order_bp.route('/all', methods=['GET'])
@admin_required
def get_all_orders(current_user):
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)
    status_filter = request.args.get('status', '')

    query = Order.query
    if status_filter and status_filter in VALID_ORDER_STATUSES:
        query = query.filter(Order.status == status_filter)

    pagination = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=limit, error_out=False
    )
    return jsonify({
        'orders': _serialize_orders(pagination.items, include_user=True),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


# -----------------------------------------------------------------------
# POST /api/orders/  — place order from cart
# -----------------------------------------------------------------------
@order_bp.route('/', methods=['POST'])
@token_required
def create_order(current_user):
    import time
    import random

    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        return jsonify({'message': 'Cart is empty'}), 400

    total_price = 0
    order_items_to_create = []

    # Calculate total and verify stock
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if not product or product.stock < item.quantity:
            return jsonify({
                'message': f'Not enough stock for "{product.name if product else f"product ID {item.product_id}"}"'
            }), 400

        item_total = product.price * item.quantity
        total_price += item_total
        product.stock -= item.quantity

        order_items_to_create.append({
            'product_id': product.id,
            'quantity': item.quantity,
            'price_at_purchase': product.price
        })

    # Create order in 'pending' state (payment processing begins)
    new_order = Order(
        user_id=current_user.id,
        total_price=round(total_price, 2),
        status='pending',
        payment_status='processing'
    )
    db.session.add(new_order)
    db.session.flush()  # get new_order.id

    for oi in order_items_to_create:
        db.session.add(OrderItem(
            order_id=new_order.id,
            product_id=oi['product_id'],
            quantity=oi['quantity'],
            price_at_purchase=oi['price_at_purchase']
        ))

    db.session.commit()  # save pending order

    # ── Simulate Payment Gateway ──────────────────────────────────────
    time.sleep(2)  # simulate network latency
    payment_success = random.random() > 0.10  # 90% success rate

    if not payment_success:
        # Revert stock
        for item in cart_items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity

        new_order.payment_status = 'failed'
        new_order.status = 'cancelled'
        db.session.commit()
        return jsonify({
            'message': 'Payment failed. Please try a different card.',
            'order_id': new_order.id
        }), 402

    # Payment succeeded — order stays 'pending' (awaiting fulfillment by admin)
    new_order.payment_status = 'paid'
    # status remains 'pending' — admin will move to shipped → delivered

    for item in cart_items:
        db.session.delete(item)

    db.session.commit()

    return jsonify({
        'message': 'Payment successful! Your order is confirmed and pending shipment.',
        'order_id': new_order.id,
        'total_price': round(total_price, 2),
        'status': 'pending'
    }), 201


# -----------------------------------------------------------------------
# PUT /api/orders/<id>/status  — admin: update order status
# -----------------------------------------------------------------------
@order_bp.route('/<int:order_id>/status', methods=['PUT'])
@admin_required
def update_order_status(current_user, order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()

    if not data or 'status' not in data:
        return jsonify({'message': 'Missing "status" field'}), 400

    new_status = data['status'].lower().strip()

    if new_status not in VALID_ORDER_STATUSES:
        return jsonify({
            'message': f'Invalid status. Must be one of: {", ".join(sorted(VALID_ORDER_STATUSES))}'
        }), 400

    if not is_valid_status_transition(order.status, new_status):
        return jsonify({
            'message': f'Cannot transition order from "{order.status}" to "{new_status}".',
            'allowed_transitions': list(
                __import__('app.utils', fromlist=['ORDER_STATUS_TRANSITIONS'])
                .ORDER_STATUS_TRANSITIONS.get(order.status, set())
            )
        }), 409

    old_status = order.status
    order.status = new_status
    db.session.commit()

    return jsonify({
        'message': f'Order #{order_id} status updated: {old_status} → {new_status}',
        'order_id': order_id,
        'old_status': old_status,
        'new_status': new_status
    }), 200


# -----------------------------------------------------------------------
# Private helpers
# -----------------------------------------------------------------------
def _serialize_orders(orders, include_user=False):
    result = []
    for order in orders:
        items = []
        for item in order.items:
            items.append({
                'product_id': item.product_id,
                'product_name': item.product.name if item.product else 'Unknown Product',
                'quantity': item.quantity,
                'price_at_purchase': item.price_at_purchase,
                'item_total': round(item.quantity * item.price_at_purchase, 2)
            })

        entry = {
            'id': order.id,
            'total_price': order.total_price,
            'status': order.status,
            'payment_status': order.payment_status,
            'created_at': order.created_at.isoformat(),
            'items': items
        }
        if include_user and order.user:
            entry['user'] = {
                'id': order.user.id,
                'name': order.user.name,
                'email': order.user.email
            }
        result.append(entry)
    return result
