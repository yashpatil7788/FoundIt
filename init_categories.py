from models import SessionLocal, Category


def add_categories():
    db = SessionLocal()
    seeds = [
        Category(name='Electronics', type='lost_found'),
        Category(name='Books', type='lost_found'),
        Category(name='Clothing', type='lost_found'),
        Category(name='Accessories', type='lost_found'),
        Category(name='Other', type='lost_found'),
        Category(name='Electronics', type='marketplace'),
        Category(name='Books', type='marketplace'),
        Category(name='Clothing', type='marketplace'),
        Category(name='Furniture', type='marketplace'),
        Category(name='Accessories', type='marketplace'),
        Category(name='Sports', type='marketplace'),
        Category(name='Services', type='marketplace'),
        Category(name='Other', type='marketplace'),
    ]

    existing = {
        (category.name, category.type)
        for category in db.query(Category).all()
    }
    missing = [category for category in seeds if (category.name, category.type) not in existing]
    if missing:
        db.add_all(missing)
        db.commit()
    db.close()
    print("Categories added.")

if __name__ == "__main__":
    add_categories()
