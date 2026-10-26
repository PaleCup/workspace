from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import random
from app.database import get_db_connection
from app.models import OrderCreate, OrderStatusUpdate

router = APIRouter(prefix="/api/orders", tags=["Orders"])

def generate_order_id():
    now_str = datetime.now().strftime("%Y%m%d")
    rand_suffix = f"{random.randint(1000, 9999)}"
    return f"ORD-{now_str}-{rand_suffix}"

@router.post("")
def create_order(payload: OrderCreate):
    if not payload.items:
        raise HTTPException(status_code=400, detail="购物车不能为空")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 校验菜品及计算总价
    dish_ids = [item.dish_id for item in payload.items]
    placeholders = ",".join("?" for _ in dish_ids)
    cursor.execute(f"SELECT id, name, price, is_available FROM dishes WHERE id IN ({placeholders})", dish_ids)
    dish_map = {row["id"]: dict(row) for row in cursor.fetchall()}

    total_amount = 0.0
    order_items_data = []

    for item in payload.items:
        if item.dish_id not in dish_map:
            conn.close()
            raise HTTPException(status_code=400, detail=f"菜品ID {item.dish_id} 不存在")
        d = dish_map[item.dish_id]
        if not d["is_available"]:
            conn.close()
            raise HTTPException(status_code=400, detail=f"菜品【{d['name']}】已售罄或已下架")
        
        subtotal = round(d["price"] * item.quantity, 2)
        total_amount += subtotal
        order_items_data.append((d["id"], d["name"], d["price"], item.quantity, subtotal))

    # 打包费计算 (外卖每份菜品2元打包费，堂食0元)
    packaging_fee = 0.0
    if payload.dining_type == "takeaway":
        total_qty = sum(item.quantity for item in payload.items)
        packaging_fee = round(min(total_qty * 1.5, 8.0), 2)  # 最高8元打包费

    total_amount = round(total_amount + packaging_fee, 2)
    order_id = generate_order_id()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO orders (
            id, dining_type, table_number, customer_name, customer_phone,
            delivery_address, remark, total_amount, packaging_fee,
            status, payment_method, payment_status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, 'paid', ?, ?)
    """, (
        order_id, payload.dining_type, payload.table_number, payload.customer_name,
        payload.customer_phone, payload.delivery_address, payload.remark,
        total_amount, packaging_fee, payload.payment_method or "wechat",
        now_str, now_str
    ))

    # 写入明细并更新菜品销量
    for dish_id, dish_name, dish_price, qty, subtotal in order_items_data:
        cursor.execute("""
            INSERT INTO order_items (order_id, dish_id, dish_name, dish_price, quantity, subtotal)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, dish_id, dish_name, dish_price, qty, subtotal))

        cursor.execute("UPDATE dishes SET monthly_sales = monthly_sales + ? WHERE id = ?", (qty, dish_id))

    conn.commit()
    conn.close()

    return {
        "message": "下单成功",
        "order_id": order_id,
        "total_amount": total_amount,
        "status": "pending"
    }

@router.get("")
def get_orders(
    status: Optional[str] = None,
    phone: Optional[str] = None,
    keyword: Optional[str] = None
):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM orders WHERE 1=1"
    params = []

    if status and status != "all":
        query += " AND status = ?"
        params.append(status)

    if phone:
        query += " AND customer_phone = ?"
        params.append(phone)

    if keyword:
        query += " AND (id LIKE ? OR customer_name LIKE ? OR table_number LIKE ?)"
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw])

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    orders = [dict(row) for row in cursor.fetchall()]

    # 关联明细
    for o in orders:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],))
        o["items"] = [dict(item) for item in cursor.fetchall()]

    conn.close()
    return orders

@router.get("/{order_id}")
def get_order_detail(order_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="订单不存在")

    order = dict(row)
    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    order["items"] = [dict(item) for item in cursor.fetchall()]

    # 查询是否有对应评价
    cursor.execute("SELECT * FROM reviews WHERE order_id = ?", (order_id,))
    rev = cursor.fetchone()
    order["review"] = dict(rev) if rev else None

    conn.close()
    return order

@router.patch("/{order_id}/status")
def update_order_status(order_id: str, payload: OrderStatusUpdate):
    valid_statuses = ["pending", "preparing", "delivering", "completed", "cancelled"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="无效的订单状态")

    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE orders SET status = ?, updated_at = ? WHERE id = ?", (payload.status, now_str, order_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="订单不存在")

    conn.commit()
    conn.close()
    return {"message": f"订单状态已更新为 {payload.status}", "order_id": order_id, "status": payload.status}
