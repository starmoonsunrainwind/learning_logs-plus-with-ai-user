import os
import django

# 核心修改：指向包含 settings.py 的文件夹名
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'II_project.settings') 
django.setup()

from django.contrib.auth.models import User

# 建议填你自己的邮箱，方便以后找回密码
USERNAME = 'admin'
PASSWORD = 'hy071126' 
EMAIL = '3356419874@qq.com' 

if not User.objects.filter(username=USERNAME).exists():
    User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
    print(f"✅ 管理员 {USERNAME} 创建成功！")
else:
    print(f"ℹ️ 管理员 {USERNAME} 已存在，跳过创建。")