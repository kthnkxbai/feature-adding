from flask import Blueprint

web_bp = Blueprint('web_root', __name__)

from .general_web_routes import general_web_bp
from .tenant_web_routes import tenant_web_bp
from .branch_web_routes import branch_web_bp
from .product_web_routes import product_web_bp

web_bp.register_blueprint(general_web_bp) 
web_bp.register_blueprint(tenant_web_bp, url_prefix="/tenants")
web_bp.register_blueprint(branch_web_bp, url_prefix="/branches")
web_bp.register_blueprint(product_web_bp, url_prefix="/products")
