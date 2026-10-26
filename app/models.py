from pydantic import BaseModel, Field
from typing import List, Optional

class MerchantUpdate(BaseModel):
    name: Optional[str] = None
    slogan: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    opening_hours: Optional[str] = None
    is_open: Optional[int] = None
    notice: Optional[str] = None
    story: Optional[str] = None
    avg_price: Optional[float] = None
    tags: Optional[List[str]] = None
    gallery: Optional[List[str]] = None

class DishCreate(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = ""
    price: float
    original_price: Optional[float] = None
    image_url: Optional[str] = ""
    tags: Optional[str] = ""
    is_available: Optional[int] = 1
    sort_order: Optional[int] = 0

class DishUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    image_url: Optional[str] = None
    tags: Optional[str] = None
    is_available: Optional[int] = None
    sort_order: Optional[int] = None

class OrderItemCreate(BaseModel):
    dish_id: int
    quantity: int

class OrderCreate(BaseModel):
    dining_type: str  # 'dine_in' or 'takeaway'
    table_number: Optional[str] = None
    customer_name: str
    customer_phone: str
    delivery_address: Optional[str] = None
    remark: Optional[str] = ""
    payment_method: Optional[str] = "wechat"
    items: List[OrderItemCreate]

class OrderStatusUpdate(BaseModel):
    status: str  # 'pending', 'preparing', 'delivering', 'completed', 'cancelled'

class ReviewCreate(BaseModel):
    order_id: Optional[str] = None
    customer_name: str
    avatar_url: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    taste_rating: int = Field(ge=1, le=5, default=5)
    service_rating: int = Field(ge=1, le=5, default=5)
    content: str
    recommended_dishes: Optional[str] = None
    tags: Optional[str] = None
    dining_type: Optional[str] = "堂食"

class ReviewReply(BaseModel):
    reply: str
