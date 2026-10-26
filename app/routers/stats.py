from fastapi import APIRouter
from datetime import datetime
from app.database import get_db_connection

router = APIRouter(prefix="/api/stats", tags=["Dashboard Statistics"])

@router.get("/dashboard")
def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    today_prefix = datetime.now().strftime("%Y-%m-%d")

    # 1. 今日营业额与订单量
    cursor.execute("""
        SELECT 
            COUNT(*) as today_orders,
            SUM(total_amount) as today_revenue
        FROM orders
        WHERE created_at LIKE ? AND status != 'cancelled'
    """, (f"{today_prefix}%",))
    today_res = cursor.fetchone()

    # 2. 待处理订单数 (pending + preparing)
    cursor.execute("""
        SELECT COUNT(*) as pending_count
        FROM orders
        WHERE status IN ('pending', 'preparing')
    """)
    pending_res = cursor.fetchone()

    # 3. 累计统计
    cursor.execute("""
        SELECT 
            COUNT(*) as total_orders,
            SUM(total_amount) as total_revenue
        FROM orders
        WHERE status != 'cancelled'
    """)
    total_res = cursor.fetchone()

    # 4. 评价概况
    cursor.execute("""
        SELECT 
            COUNT(*) as review_count,
            AVG(rating) as avg_rating,
            SUM(CASE WHEN merchant_reply IS NULL OR merchant_reply = '' THEN 1 ELSE 0 END) as unreplied_count
        FROM reviews
    """)
    review_res = cursor.fetchone()

    # 5. 热销菜品 Top 5
    cursor.execute("""
        SELECT name, monthly_sales, price, image_url
        FROM dishes
        WHERE is_available = 1
        ORDER BY monthly_sales DESC
        LIMIT 5
    """)
    top_dishes = [dict(r) for r in cursor.fetchall()]

    conn.close()

    today_orders = today_res["today_orders"] or 0
    today_revenue = round(float(today_res["today_revenue"]), 2) if today_res["today_revenue"] else 0.0
    total_orders = total_res["total_orders"] or 0
    total_revenue = round(float(total_res["total_revenue"]), 2) if total_res["total_revenue"] else 0.0

    return {
        "today_orders": today_orders,
        "today_revenue": today_revenue,
        "pending_orders": pending_res["pending_count"] or 0,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "avg_order_value": round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0,
        "review_count": review_res["review_count"] or 0,
        "avg_rating": round(float(review_res["avg_rating"]), 1) if review_res["avg_rating"] else 5.0,
        "unreplied_reviews": review_res["unreplied_count"] or 0,
        "top_dishes": top_dishes
    }
