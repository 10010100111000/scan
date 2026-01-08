# test/test_scan_flow.py
import requests
import time
import sys
import json

# === 配置区域 ===
API_BASE = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"  # 请确保与您的初始化密码一致
# 扫描目标 (建议用这个 Nmap 官方授权靶场，合法合规)
TARGET_ASSET = "scanme.nmap.org"
# 策略名称 (必须与 backend/configs/scan_strategies.yaml 中的名称完全一致)
STRATEGY_NAME = "1. 域名快速侦察 (Web)" 

def print_step(msg):
    print(f"\n{'='*10} {msg} {'='*10}")

def run_test():
    session = requests.Session()
    
    # -------------------------------------------------------------------
    # 1. 登录认证 (Auth)
    # -------------------------------------------------------------------
    print_step("1. 用户登录")
    try:
        login_resp = session.post(f"{API_BASE}/auth/login", json={
            "username": USERNAME,
            "password": PASSWORD
        })
        login_data = login_resp.json()
        
        if login_resp.status_code != 200 or login_data.get("code") != 0:
            print(f"[-] 登录失败: {login_data}")
            return

        # 获取 Token (注意：schemas.py 中定义的是 accessToken)
        token = login_data["data"]["accessToken"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        print(f"[+] 登录成功! Token: {token[:10]}...")
    except Exception as e:
        print(f"[-] 连接失败，请检查后端是否启动: {e}")
        return

    # -------------------------------------------------------------------
    # 2. 创建项目 (Projects)
    # -------------------------------------------------------------------
    print_step("2. 创建/获取项目")
    project_name = "自动化测试项目"
    
    # 先尝试创建一个新项目
    create_proj_resp = session.post(f"{API_BASE}/projects", json={"name": project_name})
    project_id = None
    
    if create_proj_resp.status_code == 200:
        # 创建成功
        p_data = create_proj_resp.json()["data"]
        project_id = p_data["id"]
        print(f"[+] 项目创建成功: ID={project_id}, Name={project_name}")
    else:
        # 可能已存在，尝试搜索获取
        print(f"[*] 项目创建返回: {create_proj_resp.status_code}，尝试查询已存在项目...")
        search_resp = session.get(f"{API_BASE}/projects", params={"search": project_name})
        projects = search_resp.json()["data"]
        if projects:
            project_id = projects[0]["id"]
            print(f"[+] 找到已有项目: ID={project_id}")
        else:
            print("[-] 无法获取项目 ID，测试终止")
            return

    # -------------------------------------------------------------------
    # 3. 创建资产 (Assets)
    # -------------------------------------------------------------------
    print_step("3. 创建资产")
    # API 变更注意：现在 project_id 是放在 body 里，而不是 url 路径里
    asset_payload = {
        "name": TARGET_ASSET,
        "type": "domain",
        "project_id": project_id
    }
    
    asset_resp = session.post(f"{API_BASE}/assets", json=asset_payload)
    asset_id = None
    
    if asset_resp.status_code in [200, 201]:
        a_data = asset_resp.json()["data"]
        asset_id = a_data["id"]
        # 如果是 200 可能是复用了已有资产，201 是新建
        msg = "资产创建成功" if asset_resp.status_code == 201 else "资产已存在(复用)"
        print(f"[+] {msg}: ID={asset_id}, Name={TARGET_ASSET}")
    else:
        print(f"[-] 资产创建失败: {asset_resp.text}")
        return

    # -------------------------------------------------------------------
    # 4. 触发扫描 (Scans)
    # -------------------------------------------------------------------
    print_step("4. 触发扫描策略")
    # API 变更注意：现在接收 asset_id 和 strategy_name
    scan_payload = {
        "asset_id": asset_id,
        "strategy_name": STRATEGY_NAME
    }
    
    scan_resp = session.post(f"{API_BASE}/scans", json=scan_payload)
    task_ids = []
    
    if scan_resp.status_code == 202:
        s_data = scan_resp.json()["data"]
        task_ids = s_data["task_ids"]
        print(f"[+] 扫描任务已下发! 生成的任务 ID: {task_ids}")
        if not task_ids:
            print("[*] 警告：没有生成新任务（可能是去重策略导致），请清理数据库后重试。")
            return
    else:
        print(f"[-] 扫描触发失败: {scan_resp.text}")
        return

    # -------------------------------------------------------------------
    # 5. 轮询任务状态 (Polling)
    # -------------------------------------------------------------------
    print_step("5. 监控任务进度")
    print("[*] 开始轮询任务状态 (按 Ctrl+C 可中断)...")
    
    # 我们只监控第一个生成的任务作为代表
    monitor_task_id = task_ids[0]
    
    try:
        while True:
            task_resp = session.get(f"{API_BASE}/tasks/{monitor_task_id}")
            if task_resp.status_code != 200:
                print(f"[-] 获取任务详情失败")
                break
                
            task_info = task_resp.json()["data"]
            status = task_info["status"]
            step_name = task_info.get("config_name", "Unknown")
            
            # 打印当前状态
            print(f" >> [Task #{monitor_task_id}] 步骤: {step_name} | 状态: {status}")
            
            if status == "completed":
                print(f"\n[+] 任务 #{monitor_task_id} 执行完成！")
                print(f"[*] 日志摘要: {task_info.get('log', '')[:100]}...")
                break
            elif status == "failed":
                print(f"\n[-] 任务 #{monitor_task_id} 失败！")
                print(f"[-] 错误日志: {task_info.get('log')}")
                break
            
            time.sleep(2) # 每2秒查一次
            
    except KeyboardInterrupt:
        print("\n[*] 用户手动停止监控")

    print_step("测试结束")
    print(f"您可以访问前端查看结果: http://localhost:5173/results/{asset_id}")

if __name__ == "__main__":
    run_test()