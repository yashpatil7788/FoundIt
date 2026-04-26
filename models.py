from datetime import datetime
from flask_login import UserMixin
from config import POSTGRES_URI, SUPABASE_URL, SUPABASE_KEY, SUPABASE_LOSTFOUND_BUCKET, SUPABASE_MARKETPLACE_BUCKET
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, Numeric, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, foreign
from supabase import create_client
import hashlib
import uuid
import mimetypes

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(POSTGRES_URI)
SessionLocal = sessionmaker(bind=engine)

# Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class User(Base, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True)
    role = Column(String, default='student')
    profile_image = Column(String)
    status = Column(String, default='active')
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    is_confirmed = Column(Boolean, default=False)
    lost_found_items = relationship('LostFoundItem', back_populates='user', foreign_keys='LostFoundItem.user_id')
    marketplace_items = relationship('MarketplaceItem', back_populates='user', foreign_keys='MarketplaceItem.user_id')

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('category.id'))

class LostFoundItem(Base):
    __tablename__ = 'lost_found_item'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    status = Column(String, nullable=False)
    priority = Column(Integer, default=1)
    date = Column(DateTime, default=datetime.utcnow)
    location = Column(String)
    contact_info = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    found_by = Column(Integer, ForeignKey('user.id'))
    claimed_by = Column(Integer, ForeignKey('user.id'))
    views = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='lost_found_items', foreign_keys=[user_id])
    images = relationship(
        'ItemImage',
        back_populates='lost_found_item',
        primaryjoin=lambda: and_(
            LostFoundItem.id == foreign(ItemImage.item_id),
            ItemImage.item_type == 'lost_found'
        )
    )

class MarketplaceItem(Base):
    __tablename__ = 'marketplace_item'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Numeric, nullable=False)
    category = Column(String)
    condition = Column(String)
    status = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    location = Column(String)
    contact_info = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    views = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='marketplace_items', foreign_keys=[user_id])
    images = relationship(
        'ItemImage',
        back_populates='marketplace_item',
        primaryjoin=lambda: and_(
            MarketplaceItem.id == foreign(ItemImage.item_id),
            ItemImage.item_type == 'marketplace'
        )
    )

class ItemImage(Base):
    __tablename__ = 'item_image'
    id = Column(Integer, primary_key=True)
    item_type = Column(String, nullable=False)  # 'lost_found' or 'marketplace'
    item_id = Column(Integer, nullable=False)
    image_url = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    lost_found_item = relationship(
        'LostFoundItem',
        back_populates='images',
        primaryjoin=lambda: and_(
            foreign(ItemImage.item_id) == LostFoundItem.id,
            ItemImage.item_type == 'lost_found'
        )
    )
    marketplace_item = relationship(
        'MarketplaceItem',
        back_populates='images',
        primaryjoin=lambda: and_(
            foreign(ItemImage.item_id) == MarketplaceItem.id,
            ItemImage.item_type == 'marketplace'
        )
    )

class Feedback(Base):
    __tablename__ = 'feedback'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    item_type = Column(String, nullable=False)  # 'lost_found' or 'marketplace'
    item_id = Column(Integer, nullable=False)
    comment = Column(Text)
    rating = Column(Integer)
    date = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = 'notification'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = 'transaction'
    id = Column(Integer, primary_key=True)
    buyer_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    seller_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    item_id = Column(Integer, ForeignKey('marketplace_item.id'), nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Log(Base):
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    action = Column(String, nullable=False)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# DB session helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_supabase_connection():
    try:
        # Try to list storage buckets (should always succeed if connected)
        res = supabase.storage.list_buckets()
        return True if isinstance(res, list) else False
    except Exception as e:
        print("Supabase connection error:", e)
        return str(e)

def upload_image_to_supabase(file, filename, bucket):
    try:
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        file_options = {"content-type": content_type}
        file_bytes = file.read()
        res = supabase.storage.from_(bucket).upload(
            path=unique_filename,
            file=file_bytes,
            file_options=file_options
        )
        # If response is UploadResponse, use .path
        if hasattr(res, 'path') and res.path:
            return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{res.path}"
        # If response is dict (error case)
        if isinstance(res, dict):
            if "error" in res and res["error"] is not None:
                raise Exception("Image upload failed: " + str(res["error"]))
            elif "data" in res and res["data"] and "path" in res["data"]:
                return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{res['data']['path']}"
        # Fallback
        raise Exception("Image upload failed (unrecognized response structure)")
    except Exception as e:
        raise Exception("Image upload failed: " + str(e))