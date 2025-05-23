import os
from app import app, db
from app.data_import import import_data
from config import Config

def init_db():
    # 确保数据库目录存在（仅当使用文件数据库时）
    if Config.DB_PATH != ':memory:':
        db_dir = os.path.dirname(Config.DB_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"Created database directory: {db_dir}")

    # 创建数据库表
    with app.app_context():
        db.create_all()
        print("Database tables created")
        import_data()
        print("Initial data imported")

if __name__ == '__main__':
    try:
        init_db()
        app.run(debug=True)
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Database path: {Config.DB_PATH}")
        print(f"Current working directory: {os.getcwd()}")
