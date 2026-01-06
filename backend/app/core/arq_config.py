# backend/app/core/arq_config.py
"""
ARQ 任务队列的配置 (Docker/Local 兼容版)
"""
import os
from arq.connections import RedisSettings

# --- Redis 配置 ---
# 优先从环境变量读取 (Docker环境), 否则使用默认值 (本地开发环境)
# 在 docker-compose.yml 中, 我们把 REDIS_HOST 设置为了 "redis"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DATABASE = 0
# REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None) # 如果有密码

redis_settings = RedisSettings(
    host=REDIS_HOST,
    port=REDIS_PORT,
    database=REDIS_DATABASE,
    # password=REDIS_PASSWORD
)

# --- ARQ 队列名称 ---
ARQ_QUEUE_NAME = "arq:queue" 

# --- ARQ 连接池管理 ---
# 用于 API 端推送任务
from arq import create_pool

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

# --- 任务函数名称常量 ---
TASK_RUN_SCAN = "run_scan_task"        # 单个任务（旧模式，保留用于重试）
TASK_RUN_STRATEGY = "run_strategy_task" # [新增] 策略任务（新模式，串行执行一组任务）