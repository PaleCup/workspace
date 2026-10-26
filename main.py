import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import merchant, dishes, orders, reviews, stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库和种子数据
    init_db()
    yield

app = FastAPI(
    title="拾味小馆 智慧餐饮与管理系统",
    description="包含订餐系统、商家信息主页与评价回复系统的全栈餐厅门户",
    version="1.0.0",
    lifespan=lifespan
)

# 允许跨域（方便开发调试）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(merchant.router)
app.include_router(dishes.router)
app.include_router(orders.router)
app.include_router(reviews.router)
app.include_router(stats.router)

# 静态资源挂载
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "拾味小馆智慧餐饮服务已启动"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
