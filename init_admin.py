import os
import django

# 1. 设置 Django 配置模块 (保持你原有的路径)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'll_project.settings')

# 2. 初始化 Django (这一步会自动加载 settings.py，进而加载环境变量)
django.setup()

from django.contrib.auth.models import User

# 3. 从环境变量读取敏感信息
# os.getenv('变量名', '默认值') 
# 如果 .env 里没写，就会用逗号后面的默认值，防止报错
USERNAME = os.getenv('ADMIN_USERNAME')
PASSWORD = os.getenv('ADMIN_PASSWORD') 
EMAIL = os.getenv('ADMIN_EMAIL')

def init_admin():
    """初始化超级管理员的函数"""
    # 检查用户是否已存在
    if not User.objects.filter(username=USERNAME).exists():
        # 创建超级用户
        User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
        print(f"✅ 管理员 {USERNAME} 创建成功！")
    else:
        print(f"ℹ️ 管理员 {USERNAME} 已存在，跳过创建。")

if __name__ == '__main__':
    init_admin()