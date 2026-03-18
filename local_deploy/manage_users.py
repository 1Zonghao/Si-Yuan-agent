# manage_users.py

from app import app, db, User

# 在这里定义你想做的修改
# 格式是： '旧名字': '新名字'
name_changes = {
    '叶宗豪': '叶师傅',
    '李昕阳': '李大人',
    '何健恺': '小何子',
    # 如果有其他需要修改的，继续在这里添加
}
# 2. 在这里定义你想添加的新用户名
new_users_to_add = [
    '新用户A',
    '新用户B',
    '新用户C'
]

# 使用 with app.app_context() 进入应用环境
with app.app_context():
    print("开始更新用户名...")
    
    # 遍历所有需要修改的名字
    for old_name, new_name in name_changes.items():
        # 在数据库中查找使用旧名字的用户
        user_to_update = User.query.filter_by(username=old_name).first()

        # 如果找到了这个用户
        if user_to_update:
            # 修改他的用户名
            user_to_update.username = new_name
            print(f"- 成功将用户 '{old_name}' 的名字修改为 '{new_name}'")
        else:
            # 如果没找到
            print(f"- 未找到名为 '{old_name}' 的用户，跳过。")

    print("开始添加新用户...")
    # --- 接着，执行添加新用户的操作 ---
    for username in new_users_to_add:
        # 检查用户是否已经存在
        existing_user = User.query.filter_by(username=username).first()
        
        # 如果用户不存在，则添加
        if not existing_user:
            new_user = User(username=username)
            db.session.add(new_user)
            print(f"- 新用户 '{username}' 已成功添加到会话。")
        else:
            # 如果用户已存在，则跳过
            print(f"- 用户 '{username}' 已存在，跳过。")
    
    # 提交所有更改到数据库
    db.session.commit()
    
    print("\n所有用户名更新完成！")
    