# tests/test_scan_flow.py
import requests
import time
import sys

# 配置
API_URL = "http://localhost:8000/api/v1"
# 请确保与 app/core/config.py 或初始化设置一致
USERNAME = "admin"
PASSWORD = "admin123" 

def get_token():
    print("[*] 正在登录获取 Token...")
    try:
        # 假设登录接口是 /auth/login (根据您的 auth.py)
        resp = requests.post(f"{API_URL}/auth/login", data={
            "username": USERNAME,
            "password": PASSWORD
        })
        if resp.status_code != 200:
            print(f"[-] 登录失败: {resp.text}")
            # 如果是第一次运行，可能需要先初始化管理员 (如果您的代码支持)
            # 或者您需要先手动在数据库插入一个用户
            return None
        return resp.json()["access_token"]
    except Exception as e:
        print(f"[-] 连接 API 失败: {e}")
        return None

def run_test():
    token = get_token()
    if not token:
        print("[-] 无法获取 Token，测试中止。请先确保数据库中有管理员账号。")
        return
    
    headers = {"Authorization": f"Bearer {token}"}

    # 1. 创建项目
    print("\n[*] 1. 创建测试项目...")
    project_payload = {"name": "毕业设计测试项目"}
    resp = requests.post(f"{API_URL}/projects", json=project_payload, headers=headers)
    
    if resp.status_code in [200, 201]:
        project_id = resp.json()["id"]
        print(f"[+] 项目创建成功, ID: {project_id}")
    elif resp.status_code == 422:
        print(f"[-] 参数验证错误: {resp.text}")
        return
    else:
        print(f"[-] 项目可能已存在或创建失败: {resp.text}")
        # 尝试查询已存在的项目
        # project_id = ...
        return

    # 2. 创建资产 (example.com)
    print("\n[*] 2. 创建根资产 (example.com)...")
    asset_payload = {"name": "example.com", "type": "domain"}
    resp = requests.post(f"{API_URL}/projects/{project_id}/assets", json=asset_payload, headers=headers)
    
    if resp.status_code in [200, 201]:
        asset_id = resp.json()["id"]
        print(f"[+] 资产创建成功, ID: {asset_id}")
    else:
        print(f"[-] 资产创建失败: {resp.text}")
        return

    # 3. 触发扫描 (Subfinder)
    print("\n[*] 3. 触发 Subfinder 扫描...")
    # 注意: config_name 必须与 scanners.yaml 中的完全一致
    scan_payload = {
        "config_name": "Subfinder (默认)"
    }
    resp = requests.post(f"{API_URL}/assets/{asset_id}/scan", json=scan_payload, headers=headers)
    
    if resp.status_code == 202:
        task_data = resp.json()
        task_id = task_data["id"] # 假设返回了任务 ID
        print(f"[+] 任务下发成功! Task ID: {task_id}")
        print(f"[*] 请观察 Docker 或 Worker 终端的日志，查看扫描进度...")
    else:
        print(f"[-] 任务下发失败: {resp.text}")

if __name__ == "__main__":
    run_test()
