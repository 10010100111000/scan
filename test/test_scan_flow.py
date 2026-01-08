# test/test_scan_flow.py
import requests
import time
import sys
import json

# === 配置区域 ===
API_BASE = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123" 
# [修改] 使用 Acunetix 官方提供的 Web 安全靶场，包含多个子域名
TARGET_ASSET = "vulnweb.com"
# 策略名称
STRATEGY_NAME = "1. 域名快速侦察 (Web)" 

def print_step(msg):
    print(f"\n{'='*10} {msg} {'='*10}")

def run_test():
    session = requests.Session()
    
    # 1. 登录
    print_step("1. 用户登录")
    try:
        login_resp = session.post(f"{API_BASE}/auth/login", json={
            "username": USERNAME,
            "password": PASSWORD
        })
        if login_resp.status_code != 200:
            print(f"[-] 登录失败: {login_resp.text}")
            return
        token = login_resp.json()["data"]["accessToken"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        print(f"[+] 登录成功! Token: {token[:10]}...")
    except Exception as e:
        print(f"[-] 连接失败: {e}")
        return

    # 2. 创建项目
    print_step("2. 创建/获取项目")
    project_name = "自动化测试项目"
    create_proj_resp = session.post(f"{API_BASE}/projects", json={"name": project_name})
    
    if create_proj_resp.status_code == 200:
        project_id = create_proj_resp.json()["data"]["id"]
        print(f"[+] 项目创建成功: ID={project_id}")
    else:
        # 如果已存在则查询
        search_resp = session.get(f"{API_BASE}/projects", params={"search": project_name})
        projects = search_resp.json()["data"]
        if projects:
            project_id = projects[0]["id"]
            print(f"[+] 使用已有项目: ID={project_id}")
        else:
            print("[-] 无法获取项目 ID")
            return

    # 3. 创建资产
    print_step(f"3. 创建根资产: {TARGET_ASSET}")
    asset_payload = {
        "name": TARGET_ASSET,
        "type": "domain",
        "project_id": project_id
    }
    asset_resp = session.post(f"{API_BASE}/assets", json=asset_payload)
    
    if asset_resp.status_code in [200, 201]:
        asset_id = asset_resp.json()["data"]["id"]
        print(f"[+] 资产准备就绪: ID={asset_id}")
    else:
        print(f"[-] 资产创建失败: {asset_resp.text}")
        return

    # 4. 触发扫描
    print_step(f"4. 触发策略: {STRATEGY_NAME}")
    scan_resp = session.post(f"{API_BASE}/scans", json={
        "asset_id": asset_id,
        "strategy_name": STRATEGY_NAME
    })
    
    if scan_resp.status_code == 202:
        task_ids = scan_resp.json()["data"]["task_ids"]
        print(f"[+] 扫描任务链已生成: {task_ids}")
        if not task_ids:
            print("[*] 提示：该资产可能近期已扫描，未生成新任务。")
            return
        
        # 5. 监控进度
        print_step("5. 实时监控任务状态")
        monitor_task_id = task_ids[0] # 监控第一个任务 (Subfinder)
        
        try:
            while True:
                task_info = session.get(f"{API_BASE}/tasks/{monitor_task_id}").json()["data"]
                status = task_info["status"]
                step = task_info.get("config_name", "Unknown")
                
                print(f" >> [Task #{monitor_task_id}] 步骤: {step} | 状态: {status}")
                
                if status == "completed":
                    print(f"\n[+] 阶段任务完成！")
                    break
                elif status == "failed":
                    print(f"\n[-] 任务失败！日志: {task_info.get('log')}")
                    break
                
                time.sleep(2)
                
            print_step("测试结束")
            print(f"请前往前端查看结果: http://localhost:8000/results/{asset_id}")
            print(f"预期结果：应发现 testphp.vulnweb.com 等子域名。")
            
        except KeyboardInterrupt:
            print("\n[*] 停止监控")
    else:
        print(f"[-] 扫描触发失败: {scan_resp.text}")

if __name__ == "__main__":
    run_test()