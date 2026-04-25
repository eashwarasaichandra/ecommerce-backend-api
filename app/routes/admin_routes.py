from flask import Blueprint, jsonify
from app.models import User, Order, OrderItem, Product
from app import db
from app.utils import admin_required
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)


# -----------------------------------------------------------------------
# GET /api/admin/stats  — dashboard summary using SQL aggregation
# -----------------------------------------------------------------------
@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_admin_stats(current_user):
    # Total users
    total_users = db.session.query(func.count(User.id)).scalar()

    # Total orders and revenue — only count paid orders
    order_stats = (
        db.session.query(
            func.count(Order.id).label('total_orders'),
            func.coalesce(func.sum(Order.total_price), 0).label('total_revenue')
        )
        .filter(Order.payment_status == 'paid')
        .first()
    )

    # Orders by status
    status_breakdown = (
        db.session.query(Order.status, func.count(Order.id).label('count'))
        .group_by(Order.status)
        .all()
    )

    # Top 5 products by units sold
    top_products = (
        db.session.query(
            Product.name,
            Product.category,
            func.sum(OrderItem.quantity).label('units_sold'),
            func.sum(OrderItem.quantity * OrderItem.price_at_purchase).label('revenue')
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.payment_status == 'paid')
        .group_by(Product.id, Product.name, Product.category)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )

    # Low stock products (stock <= 5)
    low_stock = (
        Product.query
        .filter(Product.stock <= 5)
        .order_by(Product.stock.asc())
        .all()
    )

    return jsonify({
        'summary': {
            'total_users': total_users,
            'total_orders': order_stats.total_orders,
            'total_revenue': round(float(order_stats.total_revenue), 2)
        },
        'orders_by_status': {row.status: row.count for row in status_breakdown},
        'top_products': [
            {
                'name': p.name,
                'category': p.category,
                'units_sold': int(p.units_sold),
                'revenue': round(float(p.revenue), 2)
            }
            for p in top_products
        ],
        'low_stock_alerts': [
            {'id': p.id, 'name': p.name, 'stock': p.stock, 'category': p.category}
            for p in low_stock
        ]
    }), 200
