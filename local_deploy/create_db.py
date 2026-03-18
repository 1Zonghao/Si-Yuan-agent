# create_db.py (Final Verified Version)

# 关键在于：我们只从 app.py 导入我们需要在“脚本”环境中使用的东西
# 即 app, db 和需要操作的模型 User
from app import app, db, User, Conversation, Message

# 使用 with app.app_context() 来确保所有操作都在 Flask 的“上帝视角”下进行
# 这是在外部脚本中操作 Flask 应用内数据库的标准做法
with app.app_context():
    print("进入 Flask 应用上下文...")

    # 创建所有在 app.py 中定义的、继承自 db.Model 的表
    print("正在创建所有数据库表...")
    db.create_all()
    print("数据库表创建完成。")

    # 检查并创建初始用户
    print("正在检查并创建初始用户...")
    if not User.query.filter_by(username='叶宗豪').first():
        user1 = User(username='叶宗豪')
        db.session.add(user1)
        print("- 用户 '叶宗豪' 已添加。")

    if not User.query.filter_by(username='李昕阳').first():
        user2 = User(username='李昕阳')
        db.session.add(user2)
        print("- 用户 '李昕阳' 已添加。")

    if not User.query.filter_by(username='何健恺').first():
        user3 = User(username='何健恺')
        db.session.add(user3)
        print("- 用户 '何健恺' 已添加。")

    # 提交所有更改到数据库
    db.session.commit()
    print("用户数据已提交。")

print("\n操作成功完成！siyuan.db 文件已生成，并包含初始用户。")
