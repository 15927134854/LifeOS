from dotenv import load_dotenv
import os

# 加载 .env 文件中的环境变量
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    DEBUG = bool(os.environ.get('DEBUG', True))
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # 使用内存数据库进行测试
    DB_PATH = ':memory:'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')
    
    INITIAL_VALUES_FILE = os.environ.get('INITIAL_VALUES_FILE', os.path.join(BASE_DIR, 'app', 'initial_data', 'values.json'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def init_app(cls, app):
        # 确保数据库目录存在（仅当使用文件数据库时）
        if cls.DB_PATH != ':memory:':
            db_dir = os.path.dirname(cls.DB_PATH)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
