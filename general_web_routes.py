
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
import json
import datetime


from services.tenant_service import tenant_service
from services.branch_service import branch_service
from services.product_services import product_service
from services.branch_product_module_services import branch_product_module_service
from services.feature_service import feature_service 
from services.tenant_feature_service import tenant_feature_service 


from errors import ApplicationError, NotFoundError, ValidationError

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

@general_web_bp.route('/configure_features', methods=['GET'])
def configure_features_page():
    """
    Web route to display the feature configuration page for tenants.
    """
    try:
        
        tenants = tenant_service.get_all_tenants() 

        selected_tenant_id = request.args.get('tenant_id', type=int)
        display_tenant_name = None
        enabled_features = []
        disabled_features = []

        if selected_tenant_id:
            try:
                
                selected_tenant_obj = tenant_service.get_tenant_by_id(selected_tenant_id)
                display_tenant_name = selected_tenant_obj.get('tenant_name')

                
                all_features = feature_service.get_all_features()
                tenant_features_configs = tenant_feature_service.get_all_tenant_features_for_tenant(selected_tenant_id)

                
                enabled_feature_ids = {tf['feature_id'] for tf in tenant_features_configs if tf.get('is_enabled', False)} 
                enabled_features = [f for f in all_features if f['feature_id'] in enabled_feature_ids]
                disabled_features = [f for f in all_features if f['feature_id'] not in enabled_feature_ids]

            except NotFoundError as e:
                flash(f"Tenant not found: {e.message}", "danger")
                current_app.logger.warning(f"Tenant ID {selected_tenant_id} not found for feature configuration.")
            except ApplicationError as e:
                flash(f"Error loading features for tenant: {e.message}", "danger")
                current_app.logger.error(f"Error in configure_features_page for tenant {selected_tenant_id}: {e.message}", exc_info=True)

        return render_template(
            'tf.html',
            tenants=tenants,
            selected_tenant_id=selected_tenant_id,
            display_tenant_name=display_tenant_name,
            enabled_features=enabled_features,
            disabled_features=disabled_features
        )
    except ApplicationError as e:
        flash(f"Error loading initial page data: {e.message}", "danger")
        current_app.logger.error(f"Error in configure_features_page (initial load): {e.message}", exc_info=True)
        return render_template('tf.html', tenants=[], selected_tenant_id=None, display_tenant_name=None, enabled_features=[], disabled_features=[])
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        current_app.logger.exception(f"Unexpected error in configure_features_page: {e}")
        return render_template('tf.html', tenants=[], selected_tenant_id=None, display_tenant_name=None, enabled_features=[], disabled_features=[])


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
        return redirect(url_for('web_general.index_get',
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
        return redirect(url_for('web_general.index_get',
                                 tenant_id=selected_tenant_id,
                                 branch_id=selected_branch_id,
                                 product_id=selected_product_id))

    except ApplicationError as e:
        
        flash(f"An error occurred during module configuration: {e.message}", "danger")
        current_app.logger.error(f"Error in index_post module config: {e.message}", exc_info=True)
        return redirect(url_for('web_general.index_get',
                                 tenant_id=selected_tenant_id,
                                 branch_id=selected_branch_id,
                                 product_id=selected_product_id,
                                 initial_selected_module_ids_str=submitted_module_ids_str))
    except Exception as e:
        
        current_app.logger.exception(f"Unexpected error processing module configuration in index_post: {str(e)}")
        flash(f"An unexpected error occurred during module configuration: {str(e)}", "danger")
        return redirect(url_for('web_general.index_get',
                                 tenant_id=selected_tenant_id,
                                 branch_id=selected_branch_id,
                                 product_id=selected_product_id,
                                 initial_selected_module_ids_str=submitted_module_ids_str))