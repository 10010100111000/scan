# test/test_stream_memory.py
import os
import sys
import asyncio
import psutil

# --- 关键修改：动态定位 backend 目录 ---
# 获取当前脚本所在目录 (test/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录 (test/ 的上一级)
project_root = os.path.dirname(current_dir)
# 拼接 backend 路径
backend_path = os.path.join(project_root, "backend")

# 将 backend 加入 Python 搜索路径，这样才能 import app
if backend_path not in sys.path:
    sys.path.append(backend_path)

# 现在可以正常导入后端模块了
try:
    from app.parsers.json_lines_parser import JsonLinesParser
except ImportError as e:
    print(f"[-] 导入模块失败: {e}")
    print(f"[*] 尝试的 backend 路径是: {backend_path}")
    sys.exit(1)

async def test_memory():
    # 在当前目录 (test/) 生成临时文件
    filename = os.path.join(current_dir, "large_mock_output.jsonl")
    
    print(f"[*] 1. 正在生成 10万行 模拟日志文件...")
    print(f"    -> 路径: {filename}")
    
    # 生成 50MB 左右的模拟数据
    with open(filename, "w", encoding="utf-8") as f:
        for i in range(100000):
            # 模拟 Subfinder/httpx 的 JSONL 输出
            f.write(f'{{"host": "subdomain-{i}.vulnweb.com", "ip": "192.168.1.{i%255}", "title": "Mock Title {i}", "tech": {{"Nginx": "1.18"}}}}\n')
    
    print("[*] 2. 文件生成完毕，开始流式解析测试...")
    
    # 获取当前进程
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024
    print(f"[-] 解析前内存占用: {mem_before:.2f} MB")

    # 初始化解析器
    parser = JsonLinesParser()
    # 模拟 scanners.yaml 中的映射配置
    mapping = {"hostname": "host", "ip": "ip", "title": "title"}
    
    # 模拟读取大文件
    # 注意：为了严谨测试 parser 的生成器特性，我们这里模拟流式读取
    # 实际场景中 orchestrator 也是分块处理 stdout 的
    
    count = 0
    # 这里我们读取文件内容传给 parse
    # 虽然 raw_content 本身会占内存，但我们要观察的是 parse 过程中是否 *额外* 激增了内存
    with open(filename, "r", encoding="utf-8") as f:
        raw_content = f.read()

    print("[*] 3. 进入解析循环 (使用 async generator)...")
    
    # 开始解析
    async for record in parser.parse(raw_content, mapping):
        count += 1
        if count % 20000 == 0:
            mem_curr = process.memory_info().rss / 1024 / 1024
            # 如果内存暴涨（例如超过 500MB），说明流式失败了
            print(f"    -> 已解析 {count} 行 | 当前内存: {mem_curr:.2f} MB")

    mem_after = process.memory_info().rss / 1024 / 1024
    print(f"[+] 解析完成! 总条数: {count}")
    print(f"[-] 最终内存占用: {mem_after:.2f} MB")
    
    if mem_after - mem_before < 100:
        print("[√] 测试通过：内存占用平稳，流式解析生效。")
    else:
        print("[x] 测试警告：内存占用过高。")

    # 清理垃圾文件
    if os.path.exists(filename):
        os.remove(filename)
        print("[*] 临时文件已清理")

if __name__ == "__main__":
    try:
        asyncio.run(test_memory())
    except KeyboardInterrupt:
        pass