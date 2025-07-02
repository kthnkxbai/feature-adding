from flask import Blueprint

api_bp = Blueprint('api_root', __name__, url_prefix='/api')

from .tenant_api_routes import tenant_api_bp
from .branch_api_routes import branch_api_bp
from .product_api_routes import product_api_bp
from .product_module_api_routes import product_module_api_bp
from .branch_product_module_api_routes import branch_product_module_api_bp # Assuming this is for BPM-specific routes
from .tenant_feature_api_routes import tenant_feature_api_bp # NEW


api_bp.register_blueprint(tenant_api_bp,url_prefix="/tenants")
api_bp.register_blueprint(branch_api_bp,url_prefix="/branches")
api_bp.register_blueprint(product_api_bp,url_prefix="/products")
api_bp.register_blueprint(product_module_api_bp)
api_bp.register_blueprint(branch_product_module_api_bp) # Register the BPM specific one
api_bp.register_blueprint(tenant_feature_api_bp) # NEW
