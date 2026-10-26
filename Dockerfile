FROM python:3.12-slim

WORKDIR /app

# 复制依赖清单并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码并赋予数据目录读写权限
COPY . .
RUN mkdir -p /app/data && chmod -R 777 /app/data

# 暴露默认端口
EXPOSE 8000

# 启动服务 (自动适配云平台注入的 PORT 环境变量，默认 8000)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
