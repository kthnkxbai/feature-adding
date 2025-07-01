

from flask import request, jsonify, Blueprint 
from sqlalchemy.orm import joinedload
import datetime
import traceback
import re 
import sqlalchemy 
from models import Country, Tenant, Feature, TenantFeature, Branch, Module, ProductTag, Product, ProductModule, BranchProductModule

from extensions import db

clear_trade_api_bp = Blueprint('clear_trade_api', __name__)

   
MODULE_ID_SEQUENCES = {
    1: 10,
    3: 20,
    2: 30,
    9: 40,
    5: 50,
    4: 60,
    8: 70
}    


@clear_trade_api_bp.route("/api/tenants", methods=["POST"])
def api_create_tenant():
    data = request.get_json()

    required_fields = [
        "organization_code", "tenant_name", "sub_domain",
        "default_currency", "description", "status", "country_id"
    ]
    missing = [field for field in required_fields if data.get(field) is None]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

   
    country_id_data = data["country_id"]
    country = db.session.get(Country, country_id_data)
    if country_id_data <= 0 or not country:
        return jsonify({"error": "Invalid country_id provided or country does not exist."}), 400

    organization_code = data["organization_code"]
    sub_domain = data["sub_domain"]

    
    existing_org_tenant = Tenant.query.filter_by(organization_code=organization_code).first()
    if existing_org_tenant:
        return jsonify({"error": f"Organization code '{organization_code}' already exists. Please choose a different one."}), 409 

   
    existing_sub_domain_tenant = Tenant.query.filter_by(sub_domain=sub_domain).first()
    if existing_sub_domain_tenant:
        return jsonify({"error": f"Sub-domain '{sub_domain}' already exists. Please choose a different one."}), 409 

    tenant = Tenant(
        organization_code=organization_code,
        tenant_name=data["tenant_name"],
        sub_domain=sub_domain,
        default_currency=data["default_currency"],
        description=data["description"],
        status=data["status"],
        country_id=country_id_data
    )

    try:
        db.session.add(tenant)
        db.session.commit()
        return jsonify({"message": "Tenant created successfully", "tenant_id": tenant.tenant_id}), 201
    except sqlalchemy.exc.IntegrityError as e:
        db.session.rollback()
        error_message = str(e.orig) if hasattr(e, 'orig') and e.orig else str(e)
        
        if "Duplicate entry" in error_message or "unique constraint" in error_message.lower():
            if "organization_code" in error_message:
                return jsonify({"error": f"Organization code '{organization_code}' already exists. Please choose a different one."}), 409
            elif "sub_domain" in error_message:
                return jsonify({"error": f"Sub-domain '{sub_domain}' already exists. Please choose a different one."}), 409
            else:
                return jsonify({"error": "A database integrity error occurred (e.g., duplicate entry).", "details": error_message}), 409
        return jsonify({"error": "An internal server error occurred during tenant creation", "details": error_message}), 500
    except Exception as e:
        db.session.rollback()
        import logging 
        logging.exception(f"Error creating tenant: {e}")
        return jsonify({"error": "An unexpected server error occurred", "details": str(e)}), 500


@clear_trade_api_bp.route("/api/tenants/<int:tenant_id>/<organization_code_param>/<sub_domain_param>", methods=["PUT"])
def api_update_tenant(tenant_id, organization_code_param, sub_domain_param):
   
    tenant = Tenant.query.filter_by(
        tenant_id=tenant_id,
        organization_code=organization_code_param,
        sub_domain=sub_domain_param
    ).first()

    if not tenant:
        return jsonify({"error": "Tenant not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

   
    required_fields = [
        "tenant_name", "default_currency", "description", "status", "country_id"
    ]
    missing = [field for field in required_fields if data.get(field) is None]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

   
    if 'country_id' in data:
        country_id_data = data['country_id']
        country = db.session.get(Country, country_id_data)
        if country_id_data <= 0 or not country:
            return jsonify({"error": "Invalid country_id provided or country does not exist."}), 400

    
    new_organization_code = data.get("organization_code", tenant.organization_code) 
    new_sub_domain = data.get("sub_domain", tenant.sub_domain) 
    if new_organization_code != tenant.organization_code:
        existing_org_tenant = Tenant.query.filter_by(organization_code=new_organization_code).first()
        if existing_org_tenant and existing_org_tenant.tenant_id != tenant.tenant_id: 
            return jsonify({"error": f"Organization code '{new_organization_code}' already exists for another tenant."}), 409

    
    if new_sub_domain != tenant.sub_domain:
        existing_sub_domain_tenant = Tenant.query.filter_by(sub_domain=new_sub_domain).first()
        if existing_sub_domain_tenant and existing_sub_domain_tenant.tenant_id != tenant.tenant_id: 
            return jsonify({"error": f"Sub-domain '{new_sub_domain}' already exists for another tenant."}), 409
   

   
    tenant.tenant_name = data["tenant_name"]
    tenant.default_currency = data["default_currency"]
    tenant.description = data["description"]
    tenant.status = data["status"]
    tenant.country_id = data["country_id"]
    
    tenant.organization_code = new_organization_code
    tenant.sub_domain = new_sub_domain


    try:
        db.session.commit()
        return jsonify({"message": "Tenant updated successfully"}), 200
    except sqlalchemy.exc.IntegrityError as e:
        db.session.rollback()
        error_message = str(e.orig) if hasattr(e, 'orig') and e.orig else str(e)
        
        if "Duplicate entry" in error_message or "unique constraint" in error_message.lower():
            if "organization_code" in error_message:
                return jsonify({"error": f"Organization code '{new_organization_code}' already exists."}), 409
            elif "sub_domain" in error_message:
                return jsonify({"error": f"Sub-domain '{new_sub_domain}' already exists."}), 409
            else:
                return jsonify({"error": "A database integrity error occurred (e.g., duplicate entry).", "details": error_message}), 409
        return jsonify({"error": "An internal server error occurred during tenant update", "details": error_message}), 500
    except Exception as e:
        db.session.rollback()
        import logging 
        logging.exception(f"Error updating tenant: {e}")
        return jsonify({"error": "An unexpected server error occurred", "details": str(e)}), 500


@clear_trade_api_bp.route("/api/tenants/<int:tenant_id>/<organization_code>/<sub_domain>", methods=["DELETE"])
def api_delete_tenant(tenant_id, organization_code, sub_domain):
    try:
        tenant = Tenant.query.filter_by(
            tenant_id=tenant_id,
            organization_code=organization_code,
            sub_domain=sub_domain
        ).first()

        if not tenant:
            return jsonify({
                "error": "Tenant not found",
                "details": f"Tenant with ID {tenant_id}, organization code '{organization_code}', and sub-domain '{sub_domain}' does not exist."
            }), 404

        db.session.delete(tenant)
        db.session.commit()

        return jsonify({
            "message": "Tenant deleted successfully.",
            "tenant_id": tenant_id,
            "organization_code": organization_code,
            "sub_domain": sub_domain
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred", "details": str(e)}), 500

@clear_trade_api_bp.route('/api/branches/create/<int:tenant_id>/<organization_code>/<sub_domain>', methods=["POST"])
def api_create_branch(tenant_id, organization_code, sub_domain):
    tenant = db.session.get(Tenant, (tenant_id, organization_code, sub_domain))

    if not tenant:
        return jsonify({"error": "Tenant not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    required_fields = ["name", "description", "status", "code", "country_id"]
    missing = [field for field in required_fields if data.get(field) is None]

    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    branch_code = data["code"]
    if not re.fullmatch(r"^[a-zA-Z0-9_-]+$", branch_code):
        return jsonify({"error": "Invalid branch code format. Only alphanumeric, hyphens, and underscores are allowed."}), 400

    country = db.session.get(Country, data["country_id"])
    if data["country_id"] <= 0 or not country:
        return jsonify({"error": "Invalid country_id provided or country does not exist."}), 400

    branch = Branch(
        name=data["name"],
        description=data["description"],
        status=data["status"],
        code=branch_code,
        country_id=data["country_id"],
        tenant_id=tenant_id
    )

    try:
        db.session.add(branch)
        db.session.commit()
        
        return jsonify({"message": "Branch created successfully", "branch_id": branch.branch_id}), 201
        
    except sqlalchemy.exc.IntegrityError as e:
        db.session.rollback()
        error_message = str(e.orig) if hasattr(e, 'orig') and e.orig else str(e)
        if "Duplicate entry" in error_message and "for key 'code'" in error_message:
            return jsonify({"error": f"Branch code '{branch_code}' already exists for this tenant."}), 409
        elif "foreign key constraint fails" in error_message and "fk_branch_country" in error_message:
            return jsonify({"error": "Invalid country_id provided or country does not exist."}), 400
        else:
            return jsonify({"error": "Database integrity error: " + error_message}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected server error occurred: " + str(e)}), 500


@clear_trade_api_bp.route('/api/branches/<int:branch_id>', methods=['PUT'])
def api_edit_branch(branch_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    branch = db.session.get(Branch, branch_id)
    if not branch:
        return jsonify({"error": f"Branch with ID {branch_id} not found."}), 404

    if 'name' in data:
        branch_name = data["name"]
        if not re.fullmatch(r"^[a-zA-Z0-9\s_-]+$", branch_name):
            return jsonify({"error": "Invalid branch name format. Only alphanumeric, spaces, hyphens, and underscores are allowed."}), 400

    if 'code' in data:
        branch_code = data["code"]
        if not re.fullmatch(r"^[a-zA-Z0-9_-]+$", branch_code):
            return jsonify({"error": "Invalid branch code format. Only alphanumeric, hyphens, and underscores are allowed."}), 400

    if 'country_id' in data:
        country_id = data['country_id']
        country = db.session.get(Country, country_id)
        if country_id <= 0 or not country:
            return jsonify({"error": "Invalid country_id provided or country does not exist."}), 400

    updates = {}
    for key, value in data.items():
        if hasattr(branch, key):
            if key == 'name':
                updates[key] = branch_name
            elif key == 'code':
                updates[key] = branch_code
            else:
                updates[key] = value

    for key, value in updates.items():
        setattr(branch, key, value)

    try:
        db.session.commit()
        return jsonify({"message": "Branch updated successfully", "branch_id": branch.branch_id}), 200
    except sqlalchemy.exc.IntegrityError as e:
        db.session.rollback()
        error_message = str(e.orig) if hasattr(e, 'orig') and e.orig else str(e)
        if "foreign key constraint fails" in error_message and "fk_branch_country" in error_message:
            return jsonify({"error": "Invalid country_id provided or country does not exist."}), 400
        elif "Duplicate entry" in error_message and "for key 'code'" in error_message:
            return jsonify({"error": f"Branch code already exists for this tenant."}), 409
        else:
            return jsonify({"error": "Database integrity error: " + error_message}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected server error occurred: " + str(e)}), 500

@clear_trade_api_bp.route('/api/branches/<int:branch_id>', methods=["DELETE"])
def api_delete_branch(branch_id):
    try:
        branch = db.session.get(Branch, branch_id)

        if not branch:
            return jsonify({"error": f"Branch with ID {branch_id} not found."}), 404

        db.session.delete(branch)
        db.session.commit()

        return jsonify({"message": f"Branch with ID {branch_id} deleted successfully."}), 200

    except Exception as e:
        db.session.rollback()
        if "foreign key constraint fails" in str(e).lower():
            return jsonify({"error": "Cannot delete branch: It is referenced by other records (e.g., products, reports).", "details": str(e)}), 409
        return jsonify({"error": "An internal server error occurred", "details": str(e)}), 500


@clear_trade_api_bp.route('/api/products/<int:product_id>', methods=['GET'])
def api_get_product(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": f"product with id {product_id} not found"}), 404

    product_data = {
        "product_id": product.product_id,
        "name": product.name,
        "code": product.code,
        "description": product.description,
        "tag": product.tag,
        "sequence": product.sequence,
        "parent_product_id": product.parent_product_id,
        "is_inbound": product.is_inbound,
        "product_tag_id": product.product_tag_id,
        "supported_file_formats": product.supported_file_formats
    }

    return jsonify(product_data), 200


@clear_trade_api_bp.route('/api/products', methods=['POST'])
def api_create_product():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    parent_id = data.get('parent_product_id')
    if parent_id == 0:
        parent_id = None

    product_tag_id = data.get('product_tag_id')
    if product_tag_id == 0:
        product_tag_id = None

    product = Product(
        name=data.get('name'),
        code=data.get('code'),
        description=data.get('description'),
        tag=data.get('tag'),
        sequence=data.get('sequence'),
        parent_product_id=parent_id,
        is_inbound=data.get('is_inbound', False),
        product_tag_id=product_tag_id,
        supported_file_formats=data.get('supported_file_formats')
    )
    db.session.add(product)
    db.session.commit()

    return jsonify({
        "message": "Product created",
        "product_id": product.product_id,
        "name": product.name
    }), 201

@clear_trade_api_bp.route('/api/products/<int:product_id>', methods=['PUT'])
def api_update_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": f"Product with id {product_id} not found"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    parent_id = data.get('parent_product_id')
    if parent_id == 0:
        parent_id = None

    product_tag_id = data.get('product_tag_id')
    if product_tag_id == 0:
        product_tag_id = None

    product.name = data.get('name', product.name)
    product.code = data.get('code', product.code)
    product.description = data.get('description', product.description)
    product.tag = data.get('tag', product.tag)
    product.sequence = data.get('sequence', product.sequence)
    product.parent_product_id = parent_id if parent_id != product.product_id else product.parent_product_id
    product.is_inbound = data.get('is_inbound', product.is_inbound)
    product.product_tag_id = product_tag_id
    product.supported_file_formats = data.get('supported_file_formats', product.supported_file_formats)

    db.session.commit()

    return jsonify({
        "message": "Product updated",
        "product_id": product.product_id,
        "name": product.name
    }), 200

@clear_trade_api_bp.route("/api/products/<int:product_id>", methods=["DELETE"])
def api_delete_product(product_id):
    try:
        product = db.session.get(Product, product_id)

        if not product:
            return jsonify({"error": f"Product with ID {product_id} not found."}), 404

        db.session.delete(product)
        db.session.commit()

        return jsonify({"message": f"Product with ID {product_id} deleted successfully."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred", "details": str(e)}), 500


@clear_trade_api_bp.route('/api/tenants/<int:tenant_id>/<organization_code>/<sub_domain>', methods=['GET'])
def get_tenants(tenant_id, organization_code, sub_domain):
    tenant = Tenant.query.filter_by(
        tenant_id=tenant_id,
        organization_code=organization_code,
        sub_domain=sub_domain
    ).first()

    if not tenant:
        return jsonify({"error": "Tenant not found"}), 404

    tenant_data = {
        "tenant_id": tenant.tenant_id,
        "organization_code": tenant.organization_code,
        "tenant_name": tenant.tenant_name,
        "sub_domain": tenant.sub_domain,
        "default_currency": tenant.default_currency,
        "description": tenant.description,
        "status": tenant.status,
        "country_id": tenant.country_id
    }
    return jsonify(tenant_data), 200


@clear_trade_api_bp.route('/api/tenants/<int:tenant_id>/branches', methods=['GET'])
def get_branches_by_tenants(tenant_id):
    tenant = Tenant.query.filter_by(tenant_id=tenant_id).first()

    if not tenant:
        return jsonify({"error": f"Tenant with id {tenant_id} not found"}), 404

    branches = Branch.query.filter_by(tenant_id=tenant_id).all()

    if not branches:
        return jsonify([]), 200

    branch_list = [
        {
            "branch_id": branch.branch_id,
            "name": branch.name,
            "description": branch.description,
            "status": branch.status,
            "code": branch.code,
            "country_id": branch.country_id,
            "tenant_id": branch.tenant_id
        }
        for branch in branches
    ]

    return jsonify(branch_list), 200

@clear_trade_api_bp.route('/api/products')
def get_all_productss(): 
    products = Product.query.all()
    products_data = [{"product_id": p.product_id, "name": p.name} for p in products]
    return jsonify(products_data)

@clear_trade_api_bp.route('/api/products/<int:product_id>/modules', methods=['GET'])
def get_available_product_modules_for_products(product_id):
    try:
        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({'error': f"Product with ID {product_id} not found."}), 404

        branch_id = request.args.get('branch_id', type=int)

        product_modules_for_product = ProductModule.query.options(
            joinedload(ProductModule.module)
        ).filter_by(product_id=product_id).all()

        available_module_ids = {pm.module_id for pm in product_modules_for_product}
        available_modules_info = {pm.module.module_id: pm.module for pm in product_modules_for_product if pm.module}

        configured_module_ids = set()
        if branch_id:
            configured_product_modules = db.session.query(BranchProductModule).options(
                joinedload(BranchProductModule.product_module).joinedload(ProductModule.module)
            ).filter(
                BranchProductModule.branch_id == branch_id,
                BranchProductModule.product_module.has(product_id=product_id)
            ).all()

            configured_module_ids = {bpm.product_module.module_id for bpm in configured_product_modules if bpm.product_module and bpm.product_module.module}

        modules_data = []
        for module_pk_id in available_module_ids:
            module = available_modules_info.get(module_pk_id)
            if module:
                is_configured = module.module_id in configured_module_ids
                modules_data.append({
                    'id': module.module_id,
                    'name': module.name,
                    'is_configured': is_configured
                })

        
        sorted_modules = sorted(
            modules_data,
            key=lambda item: MODULE_ID_SEQUENCES.get(item['id'], 9999)
        )
        return jsonify(sorted_modules), 200
    except Exception as e:
        
        return jsonify({'error': 'Internal server error'}), 500

@clear_trade_api_bp.route('/api/branches/<int:branch_id>/products/<int:product_id>/configured-modules', methods=['GET'])
def get_branch_products_configured_modules(branch_id, product_id):
    branch = db.session.get(Branch, branch_id)
    if not branch:
        return jsonify({'error': f"Branch with ID {branch_id} not found."}), 404

    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'error': f"Product with ID {product_id} not found."}), 404

    configured_modules = BranchProductModule.query.options(
        joinedload(BranchProductModule.product_module).joinedload(ProductModule.module)
    ).filter(
        BranchProductModule.branch_id == branch_id,
        ProductModule.product_id == product_id
    ).join(ProductModule).all()

    configured_list = []
    for bpm in configured_modules:
        if bpm.product_module and bpm.product_module.module:
            configured_list.append({
                'branch_id': bpm.branch_id,
                'product_id': bpm.product_module.product_id,
                'module_id': bpm.product_module.module.module_id,
                'module_name': bpm.product_module.module.name
            })

    
    sorted_configured_list = sorted(
        configured_list,
        key=lambda item: MODULE_ID_SEQUENCES.get(item['module_id'], 9999)
    )
    return jsonify(sorted_configured_list), 200



@clear_trade_api_bp.route('/api/config/save-product-modules', methods=['POST'])
def save_product_modules_api():
    if request.is_json:
        data = request.json
    else:
        data = request.form

    
    def get_int_value_from_data(source, key):
        value = source.get(key)
        if value is not None:
            try:
                return int(value)
            except (ValueError, TypeError):
                
                return None 
        return None

    
    selected_tenant_id = get_int_value_from_data(data, 'tenant_id')
    selected_branch_id = get_int_value_from_data(data, 'branch_id')
    selected_product_id = get_int_value_from_data(data, 'product_id')

    
    submitted_module_ids_str = data.get('module_ids_hidden', '')

    
    if selected_product_id is None or selected_branch_id is None or selected_tenant_id is None:
        return jsonify({'status': 'error', 'message': 'Missing or invalid Tenant, Branch, or Product ID format.'}), 400

    
    if not isinstance(submitted_module_ids_str, str):
        submitted_module_ids_str = str(submitted_module_ids_str)

    submitted_module_ids = {int(mid) for mid in submitted_module_ids_str.split(',') if mid.isdigit()}

    try:
        
        from models import Country, Tenant, Feature, TenantFeature, Branch, Module, ProductTag, Product, ProductModule, BranchProductModule

        tenant = Tenant.query.filter_by(tenant_id=selected_tenant_id).first()
        if not tenant:
            return jsonify({'status': 'error', 'message': f"Tenant with ID {selected_tenant_id} not found."}), 404

        branch = db.session.get(Branch, selected_branch_id)
        if not branch:
            return jsonify({'status': 'error', 'message': f"Branch with ID {selected_branch_id} not found."}), 404

        product = db.session.get(Product, selected_product_id)
        if not product:
            return jsonify({'status': 'error', 'message': f"Product with ID {selected_product_id} not found."}), 404

        all_product_modules_for_product = ProductModule.query.options(
            joinedload(ProductModule.module)
        ).filter_by(
            product_id=selected_product_id
        ).all()

        product_module_lookup_by_module_pk = {pm.module.module_id: pm for pm in all_product_modules_for_product if pm.module}
        module_name_lookup_by_module_pk = {pm.module.module_id: pm.module.name for pm in all_product_modules_for_product if pm.module}

        existing_bpms = BranchProductModule.query.options(
            joinedload(BranchProductModule.product_module)
        ).filter(
            BranchProductModule.branch_id == selected_branch_id,
            BranchProductModule.product_module.has(product_id=selected_product_id)
        ).all()

        existing_module_ids_configured = {bpm.product_module.module_id for bpm in existing_bpms if bpm.product_module and bpm.product_module.module}

        updates_made = False
        modules_added_names = []
        skipped_already_configured_names = []
        skipped_invalid_modules_ids = []

        for module_pk_id in submitted_module_ids:
            if module_pk_id not in existing_module_ids_configured:
                product_module = product_module_lookup_by_module_pk.get(module_pk_id)
                if product_module:
                    new_bpm = BranchProductModule(
                        branch_id=selected_branch_id,
                        product_module_id=product_module.product_module_id,
                        eligibility_config=None,
                        created_by=None,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(new_bpm)
                    modules_added_names.append(product_module.module.name)
                    updates_made = True
                else:
                    skipped_invalid_modules_ids.append(module_pk_id)
            else:
                module_name = module_name_lookup_by_module_pk.get(module_pk_id, f"ID {module_pk_id}")
                skipped_already_configured_names.append(module_name)

        if updates_made:
            db.session.commit()
            messages = []
            if modules_added_names:
                messages.append(f"Added modules: {', '.join(sorted(modules_added_names))}.")
            if skipped_already_configured_names:
                messages.append(f"Modules already configured (no change): {', '.join(sorted(skipped_already_configured_names))}.")
            final_message = f"Configuration updated for Product '{product.name}' at Branch '{branch.name}' for Tenant '{tenant.tenant_name or tenant.organization_code}'. " + " ".join(messages)
            return jsonify({'status': 'success', 'message': final_message, 'modules_added': modules_added_names, 'modules_skipped_configured': skipped_already_configured_names}), 200
        else:
            db.session.rollback() 
            messages = []
            if skipped_already_configured_names:
                messages.append(f"All selected modules were already configured for Product '{product.name}' at Branch '{branch.name}'. No new modules were added.")
            else:
                messages.append(f"No new modules were selected for Product '{product.name}' at Branch '{branch.name}'.")
            final_message = " ".join(messages)
            return jsonify({'status': 'info', 'message': final_message, 'modules_skipped_configured': skipped_already_configured_names}), 200

    except Exception as e:
        db.session.rollback()
        
        import logging
        logging.exception(f"Error in save_product_modules_api: {str(e)}") 
        return jsonify({'status': 'error', 'message': f"An error occurred while saving configuration: {str(e)}", 'details': str(e)}), 500



@clear_trade_api_bp.route('/api/tenants', methods=['GET'])
def get_tenantss_api():
    tenants = Tenant.query.all()
    tenants_data = [{'id': t.tenant_id, 'name': t.tenant_name} for t in tenants]
    return jsonify(tenants_data)

@clear_trade_api_bp.route('/api/tenant_features/<int:tenant_id>', methods=['GET'])
def get_tenants_features_api(tenant_id):
    try:
        enabled_features_data = []
        disabled_features_data = []

        all_features = {f.feature_id: f for f in Feature.query.all()}
        existing_tenant_features = TenantFeature.query.filter_by(tenant_id=tenant_id)\
            .options(joinedload(TenantFeature.feature)).all()

        existing_tf_map_by_feature_id = {
            tf.feature_id: tf for tf in existing_tenant_features if tf.feature is not None
        }

        for feature_id, feature in all_features.items():
            tf_entry = existing_tf_map_by_feature_id.get(feature_id)
            feature_dict = {'id': feature.feature_id, 'name': feature.name}

            if tf_entry:
                if tf_entry.is_enabled is True:
                    enabled_features_data.append(feature_dict)
                else:
                    disabled_features_data.append(feature_dict)
            else:
                enabled_features_data.append(feature_dict)

        enabled_features_data.sort(key=lambda x: x['name'].lower())
        disabled_features_data.sort(key=lambda x: x['name'].lower())

        return jsonify({
            'enabled_features': enabled_features_data,
            'disabled_features': disabled_features_data
        })

    except Exception as e:
        return jsonify({"error": f"Failed to fetch tenant features: {str(e)}"}), 500

@clear_trade_api_bp.route('/api/branches/<int:branch_id>/products/<int:product_id>/modules/<int:module_id>', methods=['DELETE'])
def api_delete_branch_product_module(branch_id, product_id, module_id):
    """
    API endpoint to delete a specific BranchProductModule entry.
    This effectively "unconfigures" a module for a given branch and product.
    """
    try:
       
        product_module = ProductModule.query.filter_by(
            product_id=product_id,
            module_id=module_id
        ).first()

        if not product_module:
            return jsonify({
                'status': 'error',
                'message': f"Product-Module combination (Product ID: {product_id}, Module ID: {module_id}) not found."
            }), 404

       
        bpm_to_delete = BranchProductModule.query.filter_by(
            branch_id=branch_id,
            product_module_id=product_module.product_module_id
        ).first()

        if not bpm_to_delete:
            return jsonify({
                'status': 'error',
                'message': f"Module {module_id} is not configured for Branch {branch_id} and Product {product_id}."
            }), 404

        db.session.delete(bpm_to_delete)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f"Module {module_id} successfully unconfigured from Branch {branch_id} for Product {product_id}."
        }), 200

    except Exception as e:
        db.session.rollback()
        import logging
        logging.exception(f"Error deleting BranchProductModule: {e}")
        return jsonify({'status': 'error', 'message': f"An error occurred during module unconfiguration: {str(e)}", 'details': str(e)}), 500


@clear_trade_api_bp.route('/api/configurations/tenant-features', methods=['POST'])
def configure_tenant_features_api():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body must be JSON and not empty'}), 400

    selected_tenant_id = data.get('tenant_id')
    enabled_feature_ids = data.get('enabled_feature_ids', [])
    disabled_feature_ids = data.get('disabled_feature_ids', [])

    
    if not isinstance(selected_tenant_id, int):
        
        try:
            selected_tenant_id = int(selected_tenant_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'tenant_id must be an integer or convertible string'}), 400

    if not isinstance(enabled_feature_ids, list):
        return jsonify({'error': 'enabled_feature_ids must be a list'}), 400
    if not isinstance(disabled_feature_ids, list):
        return jsonify({'error': 'disabled_feature_ids must be a list'}), 400

    try:
        enabled_feature_ids = [int(fid) for fid in enabled_feature_ids if isinstance(fid, int) or (isinstance(fid, str) and fid.isdigit())]
        disabled_feature_ids = [int(fid) for fid in disabled_feature_ids if isinstance(fid, int) or (isinstance(fid, str) and fid.isdigit())]
    except ValueError:
        return jsonify({'error': 'Feature ID lists must contain only integers or string representations of integers'}), 400

    if not selected_tenant_id: 
        return jsonify({"error": "Please provide a tenant_id to configure features."}), 400

    try:
        
        from models import TenantFeature, Feature 

        existing_tenant_features = TenantFeature.query.filter_by(tenant_id=selected_tenant_id).all()
        existing_tf_map = {tf.feature_id: tf for tf in existing_tenant_features}

        updates_made = False

        for feature_id in enabled_feature_ids:
            if feature_id in existing_tf_map:
                tf_entry = existing_tf_map[feature_id]
                if tf_entry.is_enabled is not True:
                    tf_entry.is_enabled = True
                    tf_entry.modified_on = datetime.datetime.utcnow() 
                    db.session.add(tf_entry)
                    updates_made = True
            else:
                new_tf = TenantFeature(
                    tenant_id=selected_tenant_id,
                    feature_id=feature_id,
                    is_enabled=True,
                    created_on=datetime.datetime.utcnow() 
                )
                db.session.add(new_tf)
                updates_made = True

        for feature_id in disabled_feature_ids:
            if feature_id in existing_tf_map:
                tf_entry = existing_tf_map[feature_id]
                if tf_entry.is_enabled is not False:
                    tf_entry.is_enabled = False
                    tf_entry.modified_on = datetime.datetime.utcnow() 
                    db.session.add(tf_entry)
                    updates_made = True
            else:
                new_tf = TenantFeature(
                    tenant_id=selected_tenant_id,
                    feature_id=feature_id,
                    is_enabled=False,
                    created_on=datetime.datetime.utcnow()
                )
                db.session.add(new_tf)
                updates_made = True

        if updates_made:
            db.session.commit()
            return jsonify({
                'message': f"Feature configurations updated successfully for Tenant ID {selected_tenant_id}!",
                'tenant_id': selected_tenant_id,
                'status': 'success'
            }), 200
        else:
            db.session.rollback()
            return jsonify({
                'message': f"No changes required or made for Tenant ID {selected_tenant_id}.",
                'tenant_id': selected_tenant_id,
                'status': 'no_change'
            }), 200

    except Exception as e:
        db.session.rollback()
        
        import logging
        logging.exception(f"Error configuring tenant features: {e}") 
        return jsonify({'error': 'An internal server error occurred', 'details': str(e)}), 500

