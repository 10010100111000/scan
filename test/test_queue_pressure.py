# test/test_queue_pressure.py
import requests
import threading
import time
import sys

# === 配置 ===
API_BASE = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
CONCURRENT_COUNT = 20  # 并发数量

def get_token():
    try:
        resp = requests.post(f"{API_BASE}/auth/login", json={
            "username": USERNAME,
            "password": PASSWORD
        })
        return resp.json()["data"]["accessToken"]
    except Exception as e:
        print(f"[-] 登录失败: {e}")
        sys.exit(1)

def create_project(token):
    # 创建一个专用项目，方便隔离
    name = f"压力测试项目_{int(time.time())}"
    resp = requests.post(f"{API_BASE}/projects", json={"name": name}, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code in [200, 201]:
        return resp.json()["data"]["id"]
    print(f"[-] 项目创建失败: {resp.text}")
    sys.exit(1)

def create_assets_batch(token, project_id, count):
    asset_ids = []
    print(f"[*] 正在预先创建 {count} 个独立资产...")
    for i in range(count):
        # 使用不同的域名绕过去重逻辑
        name = f"queue-test-{i}.local"
        resp = requests.post(f"{API_BASE}/assets", json={
            "name": name,
            "type": "domain",
            "project_id": project_id
        }, headers={"Authorization": f"Bearer {token}"})
        
        if resp.status_code in [200, 201]:
            asset_ids.append(resp.json()["data"]["id"])
    return asset_ids

def trigger_scan(index, token, asset_id):
    try:
        # 发起扫描
        resp = requests.post(f"{API_BASE}/scans", json={
            "asset_id": asset_id,
            "strategy_name": "1. 域名快速侦察 (Web)" # 确保这个策略在你的yaml里存在
        }, headers={"Authorization": f"Bearer {token}"})
        
        # 检查是否真的生成了任务
        data = resp.json().get("data", {})
        task_ids = data.get("task_ids", [])
        
        status = "成功" if task_ids else "被去重拦截"
        print(f"[{index:02d}] 资产ID={asset_id} | 状态码: {resp.status_code} | 结果: {status} | 任务数: {len(task_ids)}")
    except Exception as e:
        print(f"[{index:02d}] 请求异常: {e}")

def run():
    print("=== 开始队列压力测试 (绕过去重机制) ===")
    token = get_token()
    project_id = create_project(token)
    
    # 1. 准备数据
    asset_ids = create_assets_batch(token, project_id, CONCURRENT_COUNT)
    print(f"[+] {len(asset_ids)} 个资产准备就绪，准备并发发射！\n")
    
    # 2. 并发触发
    threads = []
    for i, asset_id in enumerate(asset_ids):
        t = threading.Thread(target=trigger_scan, args=(i, token, asset_id))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
        
    print("\n[+] 所有请求已发送。请立即查看 Worker 日志验证并发限制！")
    print("    命令: docker logs --tail 20 -f pentest_worker")

if __name__ == "__main__":
    run()