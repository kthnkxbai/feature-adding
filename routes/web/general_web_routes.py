
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
import json
import datetime


from services.tenant_service import tenant_service
from services.branch_service import branch_service
from services.product_services import product_service
from services.branch_product_module_services import branch_product_module_service
from services.feature_service import feature_service 
from services.tenant_feature_service import tenant_feature_service 


from errors import ApplicationError, NotFoundError, ValidationError, TenantNotFoundError, DatabaseOperationError, FeatureNotFoundError

general_web_bp = Blueprint('web_general', __name__)

@general_web_bp.route('/view')
def view_all_tenants():
    """
    Web route to view all tenants.
    Fetches data using the tenant_service.
    """
    try:
        
        tenants = tenant_service.get_all_tenants()
        return render_template('view.html', tenants=tenants)
    except ApplicationError as e:
        flash(f"Error loading tenants: {e.message}", "danger")
        current_app.logger.error(f"Error in view_all_tenants: {e.message}", exc_info=True)
        return render_template('view.html', tenants=[])
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        current_app.logger.exception(f"Unexpected error in view_all_tenants: {e}")
        return render_template('view.html', tenants=[])

@general_web_bp.route('/configure_features', methods=['GET']) # <--- GET-ONLY ROUTE
def configure_features_page():
    """
    Web route to display the tenant feature configuration form.
    Loads initial data for tenants and features based on selected tenant.
    """
    selected_tenant_id = request.args.get('tenant_id', type=int)
    tenants_data = []
    features_data = {'enabled_features': [], 'disabled_features': []}

    try:
        tenants_data = tenant_service.get_all_tenants(minimal=True)

        if selected_tenant_id:
            try:
                features_data = tenant_feature_service.get_features_for_tenant_with_status(selected_tenant_id)
            except (TenantNotFoundError, DatabaseOperationError, ApplicationError) as e:
                flash(f"Error loading features for tenant {selected_tenant_id}: {e.message}", "danger")
                current_app.logger.error(f"Error loading features for tenant {selected_tenant_id}: {e.message}", exc_info=True)
            except Exception as e:
                flash(f"An unexpected error occurred while loading features: {str(e)}", "danger")
                current_app.logger.exception(f"Unexpected error loading features for tenant {selected_tenant_id}: {e}")

    except (DatabaseOperationError, ApplicationError) as e:
        flash(f"Error loading initial page data: {e.message}", "danger")
        current_app.logger.error(f"Error in configure_features_page GET: {e.message}", exc_info=True)
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        current_app.logger.exception(f"Unexpected error in configure_features_page GET: {e}")

    return render_template(
        'tf.html',
        tenants=tenants_data,
        selected_tenant_id=selected_tenant_id,
        enabled_features=features_data.get('enabled_features', []),
        disabled_features=features_data.get('disabled_features', [])
    )

@general_web_bp.route('/configure_features/submit', methods=['POST']) # <--- NEW POST-ONLY ROUTE
def submit_feature_configuration():
    """
    Web route to handle the submission of the tenant feature configuration form.
    """
    selected_tenant_id = request.form.get('tenant_id', type=int)
    enabled_feature_ids_str = request.form.get('enabled_feature_ids_hidden', '')
    disabled_feature_ids_str = request.form.get('disabled_feature_ids_hidden', '')

    enabled_feature_ids = [int(fid) for fid in enabled_feature_ids_str.split(',') if fid.isdigit()]
    disabled_feature_ids = [int(fid) for fid in disabled_feature_ids_str.split(',') if fid.isdigit()]

    if not selected_tenant_id:
        flash("Please select a Tenant to configure features.", "warning")
        return redirect(url_for('web_root.web_general.configure_features_page')) # Redirect back to GET page

    try:
        result = tenant_feature_service.update_tenant_feature_configuration(
            selected_tenant_id,
            enabled_feature_ids,
            disabled_feature_ids
        )
        flash(result.get('message', 'Feature configuration updated successfully!'), result.get('status', 'success'))
    except (TenantNotFoundError, FeatureNotFoundError, ValidationError, DatabaseOperationError, ApplicationError) as e:
        flash(f"Error configuring features: {e.message}", "danger")
        current_app.logger.error(f"Error configuring tenant features: {e.message}", exc_info=True)
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        current_app.logger.exception(f"Unexpected error in submit_feature_configuration POST: {e}")

    # Always redirect back to the GET page, potentially with the selected tenant ID
    return redirect(url_for('web_root.web_general.configure_features_page', tenant_id=selected_tenant_id))


@general_web_bp.route('/', methods=['GET'])
def index_get():
    """
    Main index page web route.
    Populates dropdowns for tenant, branch, product.
    """
    try:
        tenants_data = tenant_service.get_all_tenants()
        branches_data = branch_service.get_all_branches()
        products_data = product_service.get_all_products(minimal=True) 

        modules = []
        selected_product_id = request.args.get('product_id', type=int)
        selected_branch_id = request.args.get('branch_id', type=int)
        selected_tenant_id_from_url = request.args.get('tenant_id', type=int)
        initial_selected_module_ids_str = request.args.get('initial_selected_module_ids_str', '')

        return render_template(
            'index.html',
            tenants=tenants_data,
            products=products_data,
            modules=modules, 
            branches=branches_data,
            selected_product_id=selected_product_id,
            selected_branch_id=selected_branch_id,
            selected_tenant_id_from_url=selected_tenant_id_from_url,
            module_id_sequences=current_app.config['MODULE_ID_SEQUENCES'],
            initial_selected_module_ids_str=initial_selected_module_ids_str
        )
    except ApplicationError as e:
        flash(f"Error loading page data: {e.message}", "danger")
        current_app.logger.error(f"Error in index_get: {e.message}", exc_info=True)
        return render_template('index.html', tenants=[], products=[], modules=[], branches=[],
                               selected_product_id=None, selected_branch_id=None,
                               selected_tenant_id_from_url=None, module_id_sequences={},
                               initial_selected_module_ids_str='')
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        current_app.logger.exception(f"Unexpected error in index_get: {e}")
        return render_template('index.html', tenants=[], products=[], modules=[], branches=[],
                               selected_product_id=None, selected_branch_id=None,
                               selected_tenant_id_from_url=None, module_id_sequences={},
                               initial_selected_module_ids_str='')


@general_web_bp.route('/', methods=['POST'])
def index_post():
    """
    Handles the submission of module configuration for a branch and product.
    """
    selected_tenant_id = request.form.get('tenant_id', type=int)
    selected_branch_id = request.form.get('branch_id', type=int)
    selected_product_id = request.form.get('product_id', type=int)
    submitted_module_ids_str = request.form.get('module_ids_hidden', '')
    submitted_module_ids = {int(mid) for mid in submitted_module_ids_str.split(',') if mid.isdigit()}

    if not selected_product_id or not selected_branch_id or not selected_tenant_id:
        flash("Please select a Tenant, Branch, and Product to submit.", "warning")
        return redirect(url_for('web_root.web_general.index_get',
                                 tenant_id=selected_tenant_id or '',
                                 product_id=selected_product_id or '',
                                 branch_id=selected_branch_id or ''))
    try:
        
        result = branch_product_module_service.update_branch_product_module_configuration(
            selected_branch_id,
            selected_product_id,
            submitted_module_ids
        )
        flash(result.get("message", "Module configuration updated successfully!"), "success")
        return redirect(url_for('web_root.web_general.index_get',
                                 tenant_id=selected_tenant_id,
                                 branch_id=selected_branch_id,
                                 product_id=selected_product_id))

    except ApplicationError as e:
        
        flash(f"An error occurred during module configuration: {e.message}", "danger")
        current_app.logger.error(f"Error in index_post module config: {e.message}", exc_info=True)
        return redirect(url_for('web_root.web_general.index_get',
                                 tenant_id=selected_tenant_id,
                                 branch_id=selected_branch_id,
                                 product_id=selected_product_id,
                                 initial_selected_module_ids_str=submitted_module_ids_str))
    except Exception as e:
        
        current_app.logger.exception(f"Unexpected error processing module configuration in index_post: {str(e)}")
        flash(f"An unexpected error occurred during module configuration: {str(e)}", "danger")
        return redirect(url_for('web_root.web_general.index_get',
                                 tenant_id=selected_tenant_id,
                                 branch_id=selected_branch_id,
                                 product_id=selected_product_id,
                                 initial_selected_module_ids_str=submitted_module_ids_str))