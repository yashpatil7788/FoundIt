from models import SessionLocal, Category

def add_lost_found_categories():
    db = SessionLocal()
    categories = [
        Category(name='Electronics', type='lost_found'),
        Category(name='Books', type='lost_found'),
        Category(name='Clothing', type='lost_found'),
        Category(name='Accessories', type='lost_found'),
        Category(name='Other', type='lost_found'),
    ]
    db.add_all(categories)
    db.commit()
    db.close()
    print("Lost & Found categories added.")

if __name__ == "__main__":
    add_lost_found_categories()
