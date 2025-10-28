# backend/worker.py
"""
ARQ 扫描工人 (Worker)。
这个进程会连接到 Redis, 监听任务队列, 并执行扫描任务。
"""
import asyncio

# 导入 ARQ 配置 (Redis 设置, 队列名, 任务名)
from app.core.arq_config import redis_settings, ARQ_QUEUE_NAME, TASK_RUN_SCAN

# 导入我们真正的任务执行逻辑
from app.core.orchestrator import run_scan_task_logic

# --- ARQ 任务函数 ---
# 这个函数的名字必须和 arq_config.py 中定义的 TASK_RUN_SCAN 匹配
async def run_scan_task(ctx, task_id: int):
    """
    ARQ 调用这个函数来执行扫描任务。
    'ctx' 是 ARQ 提供的上下文信息 (我们这里暂时不用)。
    'task_id' 是我们从 API 推送过来的数据库任务 ID。
    """
    print(f"Worker 收到任务: {TASK_RUN_SCAN}, task_id={task_id}")
    await run_scan_task_logic(task_id)


# --- ARQ Worker 设置 ---
class WorkerSettings:
    """
    ARQ Worker 的配置类。
    ARQ 会自动查找并使用这个类。
    """
    # 1. Redis 连接设置
    redis_settings = redis_settings

    # 2. 要监听的队列名称 (可以监听多个)
    queue_name = ARQ_QUEUE_NAME

    # 3. Worker 可以执行的任务函数列表
    functions = [run_scan_task]

    # 4. Worker 启动时执行的函数 (可选)
    async def startup(ctx):
        print("ARQ Worker 启动中...")
        # 可以在这里预加载配置或初始化资源
        from app.core.config_loader import load_scan_configs
        try:
            load_scan_configs() # 尝试加载一次, 确保配置可用
            print("扫描配置已成功预加载。")
        except Exception as e:
            print(f"警告: Worker 启动时加载扫描配置失败: {e}")
        print("ARQ Worker 已准备好接收任务。")

    # 5. Worker 关闭时执行的函数 (可选)
    async def shutdown(ctx):
        print("ARQ Worker 关闭中...")

    # 6. --- 重要的并发限制 ---
    #    限制 worker 最多同时执行多少个任务 (保护 VPS 资源)
    #    对于 2c/4g 的 VPS, 这个值需要谨慎设置, 例如 5 或 10
    max_jobs = 5 

    #    (未来可以根据任务类型进行更精细的限流, 如此处注释掉的示例)
    # job_timeout = 3_600 # 单个任务最大执行时间 (秒), 例如 1 小时
    # max_tries = 3 # 任务失败后的最大重试次数
    # keep_result_forever = False # 不永久保留成功任务的结果在 Redis 中
    # max_jobs_by_function_name = {
    #     'run_scan_task': 5, # 默认并发
    #     'run_screenshot_task': 2 # 截图任务并发限制为 2
    # }

# --- 如何运行这个 Worker ---
# 你需要在 *另一个* 终端窗口 (与运行 uvicorn 的窗口分开)
# 并且 *激活* 了 venv 虚拟环境的情况下,
# 在 backend/ 目录下, 运行以下命令来启动 worker:
#
# arq worker.WorkerSettings
#
# (或者 arq worker.WorkerSettings --verbose 来查看更详细的日志)
# Worker 会一直运行, 等待 Redis 中的新任务。