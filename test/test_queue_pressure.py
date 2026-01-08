# test/test_queue_pressure.py
import requests
import time
import threading

API_BASE = "http://localhost:8000/api/v1"
CONCURRENT_REQUESTS = 20  # 瞬间发起 20 个请求

def trigger_scan(index, token, asset_id):
    try:
        resp = requests.post(f"{API_BASE}/scans", json={
            "asset_id": asset_id,
            "strategy_name": "1. 域名快速侦察 (Web)"
        }, headers={"Authorization": f"Bearer {token}"})
        print(f"[{index}] 提交状态: {resp.status_code}")
    except Exception as e:
        print(f"[{index}] 提交失败: {e}")

def run():
    # 1. 登录
    auth = requests.post(f"{API_BASE}/auth/login", json={"username": "admin", "password": "admin123"}).json()
    token = auth["data"]["accessToken"]
    
    # 2. 获取一个资产ID (假设 ID=1 存在，或者先运行 test_scan_flow.py 创建)
    asset_id = 1 
    
    print(f"[*] 正在模拟 {CONCURRENT_REQUESTS} 个并发扫描请求...")
    threads = []
    for i in range(CONCURRENT_REQUESTS):
        t = threading.Thread(target=trigger_scan, args=(i, token, asset_id))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
        
    print("[+] 所有请求提交完毕，请检查 Worker 只有 5 个在并行！")

if __name__ == "__main__":
    run()