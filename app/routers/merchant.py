from fastapi import APIRouter, HTTPException
import json
from app.database import get_db_connection
from app.models import MerchantUpdate

router = APIRouter(prefix="/api/merchant", tags=["Merchant"])

@router.get("")
def get_merchant_info():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM merchant LIMIT 1")
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="商家信息未初始化")
    
    # 获取统计数据 (综合评分、评价数、月销总数)
    cursor.execute("SELECT COUNT(*) as review_count, AVG(rating) as avg_rating, AVG(taste_rating) as avg_taste, AVG(service_rating) as avg_service FROM reviews")
    stats = cursor.fetchone()
    
    cursor.execute("SELECT SUM(monthly_sales) as total_sales FROM dishes")
    sales_stat = cursor.fetchone()

    data = dict(row)
    data["tags"] = json.loads(data["tags"]) if data["tags"] else []
    data["gallery"] = json.loads(data["gallery"]) if data["gallery"] else []
    
    # 注入实时统计
    data["review_count"] = stats["review_count"] or 0
    data["avg_rating"] = round(float(stats["avg_rating"]), 1) if stats["avg_rating"] else 5.0
    data["avg_taste"] = round(float(stats["avg_taste"]), 1) if stats["avg_taste"] else 5.0
    data["avg_service"] = round(float(stats["avg_service"]), 1) if stats["avg_service"] else 5.0
    data["total_sales"] = sales_stat["total_sales"] or 0
    
    conn.close()
    return data

@router.put("")
def update_merchant_info(payload: MerchantUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM merchant LIMIT 1")
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="商家信息不存在")
    
    merchant_id = row["id"]
    fields = []
    values = []

    for key, val in payload.model_dump(exclude_unset=True).items():
        if key in ["tags", "gallery"] and val is not None:
            fields.append(f"{key} = ?")
            values.append(json.dumps(val, ensure_ascii=False))
        elif val is not None:
            fields.append(f"{key} = ?")
            values.append(val)

    if fields:
        values.append(merchant_id)
        sql = f"UPDATE merchant SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(sql, values)
        conn.commit()

    conn.close()
    return {"message": "商家信息更新成功"}

@router.post("/toggle-open")
def toggle_open():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, is_open FROM merchant LIMIT 1")
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="商家未找到")
    
    new_status = 0 if row["is_open"] == 1 else 1
    cursor.execute("UPDATE merchant SET is_open = ? WHERE id = ?", (new_status, row["id"]))
    conn.commit()
    conn.close()
    return {"message": "营业状态已切换", "is_open": new_status}
