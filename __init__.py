from flask import Blueprint

api_bp = Blueprint('api_root', __name__, url_prefix='/api')

from .tenant_api_routes import tenant_api_bp
from .branch_api_routes import branch_api_bp
from .product_api_routes import product_api_bp
from .product_module_api_routes import product_module_api_bp

api_bp.register_blueprint(tenant_api_bp)
api_bp.register_blueprint(branch_api_bp)
api_bp.register_blueprint(product_api_bp)
api_bp.register_blueprint(product_module_api_bp)