# backend/app/core/arq_config.py
"""
ARQ 任务队列的配置
"""
import asyncio
from arq import create_pool
from arq.connections import RedisSettings

# --- Redis 配置 ---
# 在生产环境中, 这些值应该从环境变量读取
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DATABASE = 0
# REDIS_PASSWORD = "your_redis_password" # 如果有密码

redis_settings = RedisSettings(
    host=REDIS_HOST,
    port=REDIS_PORT,
    database=REDIS_DATABASE,
    # password=REDIS_PASSWORD
)

# --- ARQ 队列名称 ---
ARQ_QUEUE_NAME = "arq:queue" # 默认队列名

# --- 用于 API 推送任务的 ARQ 连接池 ---
# (注意: worker.py 会有自己的连接方式)
arq_pool = None

async def get_arq_pool():
    """获取 ARQ 连接池 (用于 FastAPI 依赖注入)"""
    global arq_pool
    if arq_pool is None:
        arq_pool = await create_pool(redis_settings)
    return arq_pool

async def close_arq_pool():
    """关闭 ARQ 连接池 (在 FastAPI 关闭时调用)"""
    global arq_pool
    if arq_pool:
        await arq_pool.close()

# --- Worker 中将要执行的任务函数名 ---
# (我们稍后将在 worker.py 中定义这些函数)
TASK_RUN_SCAN = "run_scan_task" # 示例任务名