import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_file, send_from_directory, current_app
from flask_swagger_ui import get_swaggerui_blueprint
from flask_sqlalchemy import SQLAlchemy
from forms import TenantForm, BranchForm, ModuleForm, ProductForm, ProductModuleForm 
import json
import datetime
from flasgger import Swagger
import yaml
import traceback
import re
from flask_cors import CORS
import sqlalchemy
from werkzeug.exceptions import NotFound, HTTPException
from sqlalchemy.orm import joinedload 
from extensions import db 
from routes.web import web_bp 
from routes.api import api_bp 

from schemas.message_schemas import MessageSchema
from errors import ApplicationError, NotFoundError, ValidationError

app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:test123@localhost:3306/tenant"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "your-secret-key"
app.debug = True 
db.init_app(app)

app.config['MODULE_ID_SEQUENCES'] = {
    1: 10,
    3: 20,
    2: 30,
    9: 40,
    5: 50,
    4: 60,
    8: 70
}

from models import Country, Tenant, Feature, TenantFeature, Branch, Module, TenantReport, ReportMaster, ProductTag, Product, ProductModule, BranchProductModule

app.register_blueprint(web_bp) 
app.register_blueprint(api_bp) 

from api import clear_trade_api_bp
app.register_blueprint(clear_trade_api_bp)


SWAGGER_URL = '/swagger'
API_URL = '/static/openapi.yaml'

openapi_spec = {}
openapi_file_path = 'openapi.yaml'

try:
    with open(openapi_file_path, 'r') as f:
        openapi_spec = yaml.safe_load(f)
    print(f"OpenAPI spec loaded successfully from {openapi_file_path}")
except FileNotFoundError:
    print(f"Error: {openapi_file_path} not found. Please ensure the file is in the correct directory.")
except yaml.YAMLError as e:
    print(f"Error parsing {openapi_file_path}: {e}")

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Clear Trade API Documentation"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route(API_URL)
def serve_openapi_yaml():
    return send_from_directory(app.root_path, openapi_file_path)


@app.errorhandler(NotFoundError)
def handle_not_found_error(e):
    """Handles custom NotFoundError and returns a 404 JSON response."""
    return jsonify(message_schemas.dump({
        "status": "error",
        "message": e.message,
        "code": e.status_code,
        "details": e.errors
    })), e.status_code

@app.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handles custom ValidationError and returns a 400 JSON response."""
    return jsonify(message_schemas.dump({
        "status": "error",
        "message": e.message,
        "code": e.status_code,
        "details": e.errors 
    })), e.status_code

@app.errorhandler(ApplicationError)
def handle_application_error(e):
    """Handles general custom ApplicationError and returns an appropriate JSON response."""
    return jsonify(message_schemas.dump({
        "status": "error",
        "message": e.message,
        "code": e.status_code,
        "details": e.errors
    })), e.status_code

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Return JSON instead of HTML for general HTTP errors (e.g., 405 Method Not Allowed)."""
    return jsonify(message_schemas.dump({
        "code": e.code,
        "name": e.name,
        "description": e.description,
        "status": "error",
        "message": e.name 
    })), e.code

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    """Handle all other unexpected errors with a 500 JSON response."""
    db.session.rollback() 
    current_app.logger.exception(f"An unexpected server error occurred: {str(e)}") 
    return jsonify(message_schemas.dump({
        "status": "error",
        "message": "An unexpected server error occurred",
        "details": str(e),
        "code": 500
    })), 500
