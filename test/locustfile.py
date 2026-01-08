# test/locustfile.py
from locust import HttpUser, task, between

class AdminUser(HttpUser):
    # 模拟每个用户在操作间有 1-3 秒的思考时间
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        """每个虚拟用户启动时，先登录获取 Token"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            self.token = response.json()["data"]["accessToken"]
            # 将 Token 注入后续请求头
            self.client.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def dashboard_stats(self):
        """模拟高频刷新仪表盘 (权重3)"""
        self.client.get("/api/v1/stats/dashboard")

    @task(1)
    def task_list(self):
        """模拟查看任务列表 (权重1)"""
        self.client.get("/api/v1/tasks?limit=20")

'''
安装工具：在终端运行 pip install locust

启动测试：确保后端已运行 (docker-compose up -d)，然后运行：

使用命令:locust -f test/locustfile.py --host=http://localhost:8000
打开界面：浏览器访问 http://localhost:8089。

设置参数：

Number of users: 50 (模拟 50 人并发)

Spawn rate: 5 (每秒增加 5 人)

点击 Start swarming。

'''