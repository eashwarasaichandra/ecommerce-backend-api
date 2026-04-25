from app import create_app, db
from app.models import Product

app = create_app()

def seed_products():
    with app.app_context():
        db.create_all()
        # Check if we already have products
        if Product.query.first():
            print("Database already seeded with products.")
            return

        products = [
            Product(
                name="Premium Wireless Headphones",
                description="High-fidelity audio with active noise cancellation and 30-hour battery life.",
                price=249.99,
                stock=50,
                image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=500&q=80"
            ),
            Product(
                name="Minimalist Smartwatch",
                description="Track your fitness, notifications, and sleep with this sleek, water-resistant smartwatch.",
                price=199.50,
                stock=25,
                image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=500&q=80"
            ),
            Product(
                name="Ultra-Slim Laptop",
                description="Powerful performance in a 2.5lb aluminum chassis. 16GB RAM, 512GB SSD.",
                price=1299.00,
                stock=10,
                image_url="https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=500&q=80"
            ),
            Product(
                name="Mechanical Keyboard",
                description="RGB backlit mechanical keyboard with tactile switches for ultimate typing experience.",
                price=120.00,
                stock=100,
                image_url="https://images.unsplash.com/photo-1595225476474-87563907a212?auto=format&fit=crop&w=500&q=80"
            ),
            Product(
                name="Ergonomic Office Chair",
                description="Premium mesh back chair with lumbar support designed for long working hours.",
                price=349.99,
                stock=15,
                image_url="https://images.unsplash.com/photo-1505843490538-5133c6c7d0e1?auto=format&fit=crop&w=500&q=80"
            ),
            Product(
                name="Smartphone Gimbal",
                description="3-axis motorized gimbal stabilizer for ultra-smooth smartphone videography.",
                price=119.99,
                stock=40,
                image_url="https://images.unsplash.com/photo-1591196702657-cb391fc72a24?auto=format&fit=crop&w=500&q=80"
            )
        ]

        db.session.bulk_save_objects(products)
        db.session.commit()
        print("Successfully seeded the database with products!")

if __name__ == '__main__':
    seed_products()
