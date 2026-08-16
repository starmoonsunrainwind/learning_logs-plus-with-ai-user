import random
import dashscope
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from .models import Topic, Entry, Comment
from .ai_personas import AI_PERSONAS


dashscope.api_key = settings.DASHSCOPE_API_KEY

import re # 确保导入了正则模块
from difflib import SequenceMatcher # Python自带的相似度计算工具

# 1. 定义一个话题库 (解决"不知道说什么"的问题)
TOPIC_POOL = [
    "今天遇到的倒霉事", "推荐一部冷门电影", "如果明天是世界末日", 
    "最近吃到的神仙美食", "吐槽一下现在的天气", "小时候的零食回忆",
    "如果不考虑钱最想做什么工作", "分享一个生活小妙招", "深夜emo时刻",
    "城市里奇怪的角落", "最近在读的一本书", "对于AI的看法","分享一次出远门的经历",
    "网上评论戾气太重导致上网体验变差","加速又内卷的时代下对个人价值和归宿的思考",
    "分享遇到过的人生难题和最后的出路","生活中平凡的美好等待我们去看见","对二次元文化的看法",
    "如何看待年轻人在游戏里寻找自己的价值","维护一段交心的爱情","'我们是冠军'之后呢","聊聊最近的时政热点",
    "给你自由的两个月你会选择什么","你愿意成为一个可以得到一切的数字生命吗"
]

# 2. 定义查重函数 (解决"复读机"的问题)
def is_title_duplicate(new_title, threshold=0.6):
    """
    检查新标题是否和数据库里最近的标题太像
    threshold: 相似度阈值,0.6表示60%相似就算重复
    """
    # 获取最近10个帖子的标题
    recent_topics = Topic.objects.order_by('-date_added')[:10].values_list('text', flat=True)
    
    for old_title in recent_topics:
        # 计算相似度
        ratio = SequenceMatcher(None, new_title, old_title).ratio()
        if ratio > threshold:
            return True # 发现重复
    return False # 没发现重复
def clean_title(raw_text):
    """强制清洗标题,只保留第一句话或前15个字"""
    if not raw_text:
        return "无题"
    
    # 1. 去掉可能存在的引号、冒号
    text = raw_text.replace('"', '').replace('“', '').replace('：', ' ')
    
    # 2. 按标点符号切割，只取第一句
    sentences = re.split(r'[。！？\n]', text)
    short_title = sentences[0].strip()
    
    # 3. 如果第一句还太长，强制截断到15个字
    if len(short_title) > 15:
        short_title = short_title[:15] + "..."
        
    return short_title

def call_qwen(prompt, system_prompt):
    try:
        response = dashscope.Generation.call(
            model='qwen-plus',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
        )
        if response.status_code == 200:
            return response.output.text
        return None
    except Exception as e:
        print(f"AI 调用异常: {e}")
        return None
def create_new_post(ai_user,persona):
    
        # --- 开始循环尝试生成标题 ---
        final_title = None
        max_retries = 10 # 最多尝试3次
        
        for attempt in range(max_retries):
            # 1. 从话题库里随机抽一个签 (方案一)
            random_topic_seed = random.choice(TOPIC_POOL)
            
            # 2. 构造 Prompt，要求 AI 基于这个签生成标题 (方案一的强化版)
            prompt = f"""
            你是一个论坛用户。请围绕【{random_topic_seed}】这个方向，想一个极简短的帖子标题（15字以内）。
            要求：
            1. 语气要符合 {persona['display_name']} 的人设。
            2. 标题要新颖，不要陈词滥调。
            """
            
            # 3. 调用 AI
            raw_title = call_qwen(prompt,persona['system_prompt'])
            title = clean_title(raw_title) # 使用你原有的清洗函数
            
            # 4. 【关键】代码级查重 (方案二)
            if not is_title_duplicate(title):
                final_title = title
                print(f"✅ 标题生成成功且无重复: {title}")
                break # 成功了，跳出循环
            else:
                print(f"⚠️ 标题 '{title}' 与近期内容重复，正在重试 ({attempt+1}/{max_retries})...")

        # --- 循环结束，判断结果 ---
        if final_title:
            # 创建 Topic
            new_topic = Topic.objects.create(
                text=final_title,
                owner=ai_user,
                public=True
            )
            
            # 针对这个标题写正文 (保持你原来的逻辑即可)
            entry_content = call_qwen(
                f"请以 {persona['display_name']} 的身份，针对【{final_title}】这个话题，写一段详细的心得体会。你的看法尽量真实，且不一定与你的兴趣爱好相关，如果与爱好相关，请不要太专业化。{persona['system_prompt']}",
            persona['system_prompt'])
            
            if entry_content:
                Entry.objects.create(
                    topic=new_topic,
                    text=entry_content,
                )
                print(f"🎉 成功发布新主题: {final_title}")
        else:
            print("❌ 尝试多次后仍无法生成不重复的标题，本次放弃发帖。")

def ai_daily_routine():
    """Django-Q 定时调用的主函数"""
    print(">>> AI 开始每日巡查...")
    
    # 1. 随机选择一个 AI 账号
    ai_key = random.choice(list(AI_PERSONAS.keys()))
    persona = AI_PERSONAS[ai_key]
    
    # 2. 【核心】获取或创建用户，username 直接使用带 [AI] 标记的名字
    ai_user, created = User.objects.get_or_create(username=persona['display_name'])
        # ... 前面的代码 (User获取等) ...
    

    # 随机决定行为权重：
    # 1. 'new_post': 发全新的主题
    # 2. 'update_old': 在自己以前的主题下补充条目
    # 3. 'comment': 去别人的主题下评论
    action = random.choices(
        ['new_post', 'update_old', 'comment'], 
        weights=[20, 40, 40],  # 这里可以调整概率
        k=1
    )[0]

    # ================= 情况 A：发布全新主题 =================
    # ... 前面的代码 ...
        # ... 前面的代码 ...
    
    if action == 'new_post':
        print(f"🤖 [{persona['display_name']}] 决定发布一个新主题...")
        create_new_post(ai_user=ai_user,persona=persona)
    # ... 后面的 update_old 代码 ...

    # ================= 情况 B：在自己旧主题下更新 (新功能) =================
    elif action == 'update_old':
        print(f"🤖 [{persona['display_name']}] 决定在自己的旧主题下更新内容...")
        
        # 查找该 AI 用户以前发布的公开主题
        my_topics = Topic.objects.filter(owner=ai_user, public=True)
        
        if my_topics.exists():
            # 随机选一个旧主题
            target_topic = random.choice(my_topics)
            
            prompt = f"你之前发起了关于【{target_topic.text}】的讨论。现在请你以{persona['display_name']}的身份，在这个话题下补充一些新的看法或后续进展。你的看法尽量真实，语言风格与你的设定一致，具体内容不用与你的兴趣爱好强行相关，如果与爱好相关，请不要太专业化。"
            
            entry_content = call_qwen(prompt, persona['system_prompt'])
            
            if entry_content:
                Entry.objects.create(
                    topic=target_topic,
                    text=entry_content,
                    )
                print(f"✅ 成功在旧主题 [{target_topic.text}] 下更新了条目。")
        else:
            print("⚠️ 该用户还没有旧主题，选择发布一个主题")
            create_new_post(ai_user=ai_user,persona=persona)

    # ================= 情况 C：去别人地盘评论 =============
            
    elif action == 'comment':
        # 寻找最近的一条公开条目（排除 AI 自己发的）
        target_entry = Entry.objects.filter(topic__public=True).exclude(topic__owner=ai_user).order_by('-date_added').first()
        if target_entry:
            comment_text = call_qwen(f"阅读笔记'{target_entry.text[:500]}...'，请以你的身份发表一段评论。评论尽量真实，语言风格需要与设定一致，但具体内容不必强行与兴趣爱好相关，如果与爱好相关，请不要太专业化。", persona['system_prompt'])
            if comment_text:
                Comment.objects.create(entry=target_entry, owner=ai_user, text=comment_text)
                print(f"[{persona['display_name']}] 评论了条目 ID: {target_entry.id}")
        else:
            print("暂无合适的公开条目可供评论。")
        