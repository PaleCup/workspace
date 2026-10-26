from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import get_db_connection
from app.models import DishCreate, DishUpdate

router = APIRouter(prefix="/api", tags=["Dishes & Categories"])

@router.get("/categories")
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, COUNT(d.id) as dish_count
        FROM categories c
        LEFT JOIN dishes d ON c.id = d.category_id AND d.is_available = 1
        GROUP BY c.id
        ORDER BY c.sort_order ASC, c.id ASC
    """)
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return categories

@router.post("/categories")
def add_category(name: str = Query(...), icon: Optional[str] = "utensils"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO categories (name, icon) VALUES (?, ?)", (name, icon))
    conn.commit()
    cat_id = cursor.lastrowid
    conn.close()
    return {"id": cat_id, "name": name, "icon": icon}

@router.get("/dishes")
def get_dishes(
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    admin: bool = False
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT d.*, c.name as category_name 
        FROM dishes d
        JOIN categories c ON d.category_id = c.id
        WHERE 1=1
    """
    params = []
    
    if not admin:
        query += " AND d.is_available = 1"
        
    if category_id:
        query += " AND d.category_id = ?"
        params.append(category_id)
        
    if keyword:
        query += " AND (d.name LIKE ? OR d.description LIKE ? OR d.tags LIKE ?)"
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw])
        
    query += " ORDER BY d.sort_order ASC, d.id ASC"
    
    cursor.execute(query, params)
    dishes = [dict(row) for row in cursor.fetchall()]
    
    # 将tags转换为list
    for d in dishes:
        d["tag_list"] = [t.strip() for t in d["tags"].split(",") if t.strip()] if d["tags"] else []

    conn.close()
    return dishes

@router.get("/dishes/{dish_id}")
def get_dish(dish_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*, c.name as category_name
        FROM dishes d
        JOIN categories c ON d.category_id = c.id
        WHERE d.id = ?
    """, (dish_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="菜品不存在")
    data = dict(row)
    data["tag_list"] = [t.strip() for t in data["tags"].split(",") if t.strip()] if data["tags"] else []
    return data

@router.post("/dishes")
def create_dish(payload: DishCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO dishes (
            category_id, name, description, price, original_price,
            image_url, tags, is_available, sort_order
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.category_id, payload.name, payload.description,
        payload.price, payload.original_price, payload.image_url,
        payload.tags, payload.is_available, payload.sort_order
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"message": "菜品创建成功", "id": new_id}

@router.put("/dishes/{dish_id}")
def update_dish(dish_id: int, payload: DishUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for k, v in payload.model_dump(exclude_unset=True).items():
        fields.append(f"{k} = ?")
        values.append(v)
        
    if not fields:
        conn.close()
        return {"message": "无需更新"}
        
    values.append(dish_id)
    sql = f"UPDATE dishes SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(sql, values)
    conn.commit()
    conn.close()
    return {"message": "菜品已更新"}

@router.patch("/dishes/{dish_id}/toggle-status")
def toggle_dish_status(dish_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_available FROM dishes WHERE id = ?", (dish_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="菜品不存在")
        
    new_status = 0 if row["is_available"] == 1 else 1
    cursor.execute("UPDATE dishes SET is_available = ? WHERE id = ?", (new_status, dish_id))
    conn.commit()
    conn.close()
    return {"message": "状态已更新", "is_available": new_status}

@router.delete("/dishes/{dish_id}")
def delete_dish(dish_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dishes WHERE id = ?", (dish_id,))
    conn.commit()
    conn.close()
    return {"message": "菜品已删除"}
