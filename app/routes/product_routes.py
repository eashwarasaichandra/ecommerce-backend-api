from flask import Blueprint, request, jsonify
from app.models import Product, Review
from app import db
from app.utils import admin_required, token_required

product_bp = Blueprint('products', __name__)

@product_bp.route('/', methods=['GET'])
def get_products():
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    query = Product.query
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))
    if category_filter:
        query = query.filter(Product.category == category_filter)
        
    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    products = pagination.items
    
    result = []
    for p in products:
        result.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'category': p.category,
            'price': p.price,
            'stock': p.stock,
            'image_url': p.image_url
        })
        
    return jsonify({
        'products': result,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    p = Product.query.get_or_404(product_id)
    
    reviews = []
    for r in p.reviews:
        reviews.append({
            'user': r.user.name,
            'rating': r.rating,
            'comment': r.comment,
            'date': r.created_at.isoformat()
        })
        
    return jsonify({
        'id': p.id,
        'name': p.name,
        'category': p.category,
        'description': p.description,
        'price': p.price,
        'stock': p.stock,
        'image_url': p.image_url,
        'reviews': reviews
    }), 200

@product_bp.route('/', methods=['POST'])
@admin_required
def add_product(current_user):
    data = request.get_json()
    if not data or not data.get('name') or not data.get('price'):
        return jsonify({'message': 'Missing required fields'}), 400
        
    new_product = Product(
        name=data['name'],
        category=data.get('category', 'Other'),
        description=data.get('description', ''),
        price=data['price'],
        stock=data.get('stock', 0),
        image_url=data.get('image_url', '')
    )
    
    db.session.add(new_product)
    db.session.commit()
    
    return jsonify({'message': 'Product created successfully!', 'id': new_product.id}), 201

@product_bp.route('/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(current_user, product_id):
    p = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if 'name' in data:
        p.name = data['name']
    if 'category' in data:
        p.category = data['category']
    if 'description' in data:
        p.description = data['description']
    if 'price' in data:
        p.price = data['price']
    if 'stock' in data:
        p.stock = data['stock']
    if 'image_url' in data:
        p.image_url = data['image_url']
        
    db.session.commit()
    return jsonify({'message': 'Product updated successfully!'}), 200

@product_bp.route('/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(current_user, product_id):
    p = Product.query.get_or_404(product_id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully!'}), 200

@product_bp.route('/<int:product_id>/reviews', methods=['POST'])
@token_required
def add_review(current_user, product_id):
    p = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if not data or 'rating' not in data:
        return jsonify({'message': 'Rating is required'}), 400
        
    new_review = Review(
        user_id=current_user.id,
        product_id=p.id,
        rating=int(data['rating']),
        comment=data.get('comment', '')
    )
    db.session.add(new_review)
    db.session.commit()
    return jsonify({'message': 'Review added successfully!'}), 201
