# backend/worker.py
"""
ARQ 扫描工人 (Worker)。
这个进程会连接到 Redis, 监听任务队列, 并执行扫描任务。
"""
import asyncio

# 导入 ARQ 配置
from app.core.arq_config import redis_settings, ARQ_QUEUE_NAME, TASK_RUN_SCAN, TASK_RUN_STRATEGY

# 导入我们真正的任务执行逻辑
from app.core.orchestrator import run_scan_task_logic

# --- 1. 单个任务执行函数 (保留) ---
async def run_scan_task(ctx, task_id: int):
    """
    执行单个扫描任务。通常用于由 run_strategy_task 内部调用，
    或者用于后台手动“重试”某个特定失败的步骤。
    """
    print(f"[Worker] 开始执行单任务: {task_id}")
    await run_scan_task_logic(task_id)

# --- 2. [新增] 策略组执行函数 (串行核心) ---
async def run_strategy_task(ctx, task_ids: list[int]):
    """
    接收一组任务 ID，按顺序串行执行。
    这解决了 Subfinder 还没入库，httpx 就开始跑的竞争问题。
    """
    print(f"[Worker] 收到策略组任务，包含 {len(task_ids)} 个步骤: {task_ids}")
    
    for index, task_id in enumerate(task_ids):
        step_num = index + 1
        print(f">>> [策略进度 {step_num}/{len(task_ids)}] 正在启动任务 ID: {task_id}")
        
        try:
            # 关键点：这里使用 await，必须等上一步完全结束（含入库），才会循环到下一步
            await run_scan_task_logic(task_id)
        except Exception as e:
            print(f"!!! 任务 {task_id} 执行异常: {e}")
            # 决策点：如果中间一步失败了，是否继续？
            # 目前逻辑：打印错误，继续尝试下一步（或者你可以选择在这里 break 停止后续步骤）
    
    print(f"[Worker] 策略组执行完毕: {task_ids}")

# --- ARQ Worker 设置 ---
class WorkerSettings:
    redis_settings = redis_settings
    queue_name = ARQ_QUEUE_NAME

    # 注册两个函数，Worker 既能跑单任务，也能跑策略组
    functions = [run_scan_task, run_strategy_task]

    async def startup(ctx):
        print("ARQ Worker 启动中...")
        from app.core.config_loader import load_scan_configs
        try:
            load_scan_configs()
            print("扫描配置已成功预加载。")
        except Exception as e:
            print(f"警告: Worker 启动时加载扫描配置失败: {e}")

    async def shutdown(ctx):
        print("ARQ Worker 关闭中...")

    # 并发限制
    max_jobs = 5