
import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "mysql+pymysql://root:test123@localhost:3306/tenant")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-please-change-in-production")
   
    API_TITLE = "Clear Trade API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.2"
    OPENAPI_URL_PREFIX = "/docs"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

   
    MODULE_ID_SEQUENCES = {
        1: 10, 3: 20, 2: 30, 9: 40, 5: 50, 4: 60, 8: 70
    }
