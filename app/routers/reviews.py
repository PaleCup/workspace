from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
from app.database import get_db_connection
from app.models import ReviewCreate, ReviewReply

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])

@router.get("")
def get_reviews(
    filter_type: Optional[str] = "all",  # all, positive (4-5), critical (1-2), with_reply, unreplied
    dining_type: Optional[str] = None
):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM reviews WHERE 1=1"
    params = []

    if filter_type == "positive":
        query += " AND rating >= 4"
    elif filter_type == "critical":
        query += " AND rating <= 2"
    elif filter_type == "unreplied":
        query += " AND (merchant_reply IS NULL OR merchant_reply = '')"
    elif filter_type == "with_reply":
        query += " AND (merchant_reply IS NOT NULL AND merchant_reply != '')"

    if dining_type:
        query += " AND dining_type = ?"
        params.append(dining_type)

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    reviews = [dict(row) for row in cursor.fetchall()]

    for r in reviews:
        r["tag_list"] = [t.strip() for t in r["tags"].split(",") if t.strip()] if r["tags"] else []
        r["rec_dishes"] = [d.strip() for d in r["recommended_dishes"].split(",") if d.strip()] if r["recommended_dishes"] else []

    conn.close()
    return reviews

@router.get("/stats")
def get_review_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COUNT(*) as total_count,
            AVG(rating) as avg_rating,
            AVG(taste_rating) as avg_taste,
            AVG(service_rating) as avg_service,
            SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) as star_5,
            SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) as star_4,
            SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) as star_3,
            SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) as star_2,
            SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as star_1,
            SUM(CASE WHEN merchant_reply IS NOT NULL AND merchant_reply != '' THEN 1 ELSE 0 END) as replied_count
        FROM reviews
    """)
    row = cursor.fetchone()
    
    total = row["total_count"] or 0
    stats = {
        "total_count": total,
        "avg_rating": round(float(row["avg_rating"]), 1) if row["avg_rating"] else 5.0,
        "avg_taste": round(float(row["avg_taste"]), 1) if row["avg_taste"] else 5.0,
        "avg_service": round(float(row["avg_service"]), 1) if row["avg_service"] else 5.0,
        "replied_count": row["replied_count"] or 0,
        "unreplied_count": total - (row["replied_count"] or 0),
        "stars": {
            5: {"count": row["star_5"] or 0, "pct": round(((row["star_5"] or 0) / total * 100) if total else 0, 1)},
            4: {"count": row["star_4"] or 0, "pct": round(((row["star_4"] or 0) / total * 100) if total else 0, 1)},
            3: {"count": row["star_3"] or 0, "pct": round(((row["star_3"] or 0) / total * 100) if total else 0, 1)},
            2: {"count": row["star_2"] or 0, "pct": round(((row["star_2"] or 0) / total * 100) if total else 0, 1)},
            1: {"count": row["star_1"] or 0, "pct": round(((row["star_1"] or 0) / total * 100) if total else 0, 1)}
        }
    }

    conn.close()
    return stats

@router.post("")
def create_review(payload: ReviewCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 随机头像如果不提供
    default_avatars = [
        "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=100&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=100&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&auto=format&fit=crop&q=80"
    ]
    import random
    avatar = payload.avatar_url or random.choice(default_avatars)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO reviews (
            order_id, customer_name, avatar_url, rating, taste_rating,
            service_rating, content, recommended_dishes, tags, dining_type, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.order_id, payload.customer_name, avatar,
        payload.rating, payload.taste_rating, payload.service_rating,
        payload.content, payload.recommended_dishes, payload.tags,
        payload.dining_type or "堂食", now_str
    ))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return {"message": "评价发表成功", "id": new_id}

@router.post("/{review_id}/reply")
def reply_review(review_id: int, payload: ReviewReply):
    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE reviews SET merchant_reply = ?, replied_at = ? WHERE id = ?
    """, (payload.reply, now_str, review_id))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="评价不存在")

    conn.commit()
    conn.close()
    return {"message": "回复成功", "replied_at": now_str}

@router.delete("/{review_id}")
def delete_review(review_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    return {"message": "评价已删除"}
