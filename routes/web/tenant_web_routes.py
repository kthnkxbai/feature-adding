from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from forms import TenantForm

from services.tenant_service import tenant_service
from services.country_service import country_service

from errors import ValidationError, DuplicateOrganizationCodeError, DuplicateSubDomainError, \
    TenantNotFoundError, ApplicationError, NotFoundError, DatabaseOperationError

tenant_web_bp = Blueprint('web_tenant', __name__)

@tenant_web_bp.route("/", methods=["GET"])
def show_tenant_creation_form():
    """
    Web route to display the form for creating a new tenant.
    """
    form = TenantForm()
    try:
        countries = country_service.get_all_countries() 
        form.country_id.choices = [(c['country_id'], c['country_name']) for c in countries]
    except ApplicationError as e:
        flash(f"Error loading countries: {e.message}", "danger")
        current_app.logger.error(f"Error loading countries for tenant form: {e.message}", exc_info=True)
        form.country_id.choices = [] 
    except Exception as e:
        flash(f"An unexpected error occurred while loading countries: {str(e)}", "danger")
        current_app.logger.exception(f"Unexpected error loading countries for tenant form: {e}")
        form.country_id.choices = []
    return render_template("tenant_form.html", form=form)

@tenant_web_bp.route("/", methods=["POST"])
def create_tenant():
    """
    Web route to handle submission of the tenant creation form.
    """
    form = TenantForm()
    try:
        countries = country_service.get_all_countries()
        form.country_id.choices = [(c['country_id'], c['country_name']) for c in countries]
    except ApplicationError as e:
        flash(f"Error loading countries: {e.message}", "danger")
        current_app.logger.error(f"Error loading countries for tenant form (POST): {e.message}", exc_info=True)
        form.country_id.choices = []
    except Exception as e:
        flash(f"An unexpected error occurred while loading countries: {str(e)}", "danger")
        current_app.logger.exception(f"Unexpected error loading countries for tenant form (POST): {e}")
        form.country_id.choices = []

    if form.validate_on_submit():
        tenant_data = {
            'organization_code': form.organization_code.data,
            'tenant_name': form.tenant_name.data,
            'sub_domain': form.sub_domain.data,
            'default_currency': form.default_currency.data,
            'description': form.description.data,
            'status': form.status.data,
            'country_id': form.country_id.data
        }
        try:
            new_tenant = tenant_service.create_tenant(tenant_data)
            flash(f"Tenant '{new_tenant['tenant_name']}' created successfully!", "success")
            return redirect(url_for('web_root.web_general.index_get'))
        except (ValidationError, DuplicateOrganizationCodeError, DuplicateSubDomainError, TenantNotFoundError, DatabaseOperationError, ApplicationError) as e:
            flash(f"Error creating tenant: {e.message}", "danger")
            current_app.logger.error(f"Error creating tenant: {e.message}", exc_info=True)
            return render_template("tenant_form.html", form=form)
        except Exception as e:
            current_app.logger.exception(f"Unexpected error in create_tenant POST: {str(e)}")
            flash(f"An unexpected error occurred: {str(e)}", "danger")
            return render_template("tenant_form.html", form=form)
    return render_template("tenant_form.html", form=form)

@tenant_web_bp.route("/<int:tenant_id>/<organization_code>/<sub_domain>", methods=["GET"])
def show_update_tenant_form(tenant_id, organization_code, sub_domain):
    """
    Web route to display the form for updating an existing tenant.
    """
    tenant_data = None
    try:
        tenant_data = tenant_service.get_tenant_by_composite_pk(tenant_id, organization_code, sub_domain)
        class DictAsObj:
            def __init__(self, dictionary):
                for key, value in dictionary.items():
                    setattr(self, key, value)
        tenant_obj = DictAsObj(tenant_data)

        form = TenantForm(obj=tenant_obj)

        countries = country_service.get_all_countries()
        form.country_id.choices = [(c['country_id'], c['country_name']) for c in countries]
        form.country_id.data = tenant_data.get('country_id') 

        return render_template("update.html", form=form, tenant=tenant_data)
    except (TenantNotFoundError, DatabaseOperationError, ApplicationError) as e:
        flash(f"Error loading tenant for update: {e.message}", "danger")
        current_app.logger.error(f"Error loading tenant for update form: {e.message}", exc_info=True)
        return redirect(url_for('web_root.web_general.index_get'))
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in show_update_tenant_form: {str(e)}")
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        return redirect(url_for('web_root.web_general.index_get'))


@tenant_web_bp.route("/<int:tenant_id>/<organization_code_param>/<sub_domain_param>", methods=["POST"])
def process_update_tenant_form(tenant_id, organization_code_param, sub_domain_param):
    """
    Web route to process the submission of the tenant update form.
    """
    tenant_data_before_update = None
    try:
        tenant_data_before_update = tenant_service.get_tenant_by_composite_pk(tenant_id, organization_code_param, sub_domain_param)
    except (TenantNotFoundError, DatabaseOperationError, ApplicationError) as e:
        flash(f"Tenant not found for update: {e.message}", "danger")
        current_app.logger.error(f"Tenant not found for update form (POST): {e.message}", exc_info=True)
        return redirect(url_for('web_root.web_general.index_get'))
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in process_update_tenant_form (pre-load): {str(e)}")
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        return redirect(url_for('web_root.web_general.index_get'))

    form = TenantForm(request.form)
    try:
        countries = country_service.get_all_countries()
        form.country_id.choices = [(c['country_id'], c['country_name']) for c in countries]
    except ApplicationError as e:
        flash(f"Error loading countries: {e.message}", "danger")
        current_app.logger.error(f"Error loading countries for tenant form (POST): {e.message}", exc_info=True)
        form.country_id.choices = []
    except Exception as e:
        flash(f"An unexpected error occurred while loading countries: {str(e)}", "danger")
        current_app.logger.exception(f"Unexpected error loading countries for tenant form (POST): {e}")
        form.country_id.choices = []

    if form.validate_on_submit():
        update_data = {
            'organization_code': form.organization_code.data,
            'tenant_name': form.tenant_name.data,
            'sub_domain': form.sub_domain.data,
            'default_currency': form.default_currency.data,
            'description': form.description.data,
            'status': form.status.data,
            'country_id': form.country_id.data
        }
        try:
            updated_tenant = tenant_service.update_tenant(tenant_id, organization_code_param, sub_domain_param, update_data)
            flash(f"Tenant '{updated_tenant['tenant_name']}' updated successfully!", "success")
            return redirect(url_for('web_root.web_general.index_get'))
        except (ValidationError, DuplicateOrganizationCodeError, DuplicateSubDomainError, TenantNotFoundError, DatabaseOperationError, ApplicationError) as e:
            flash(f"Error updating tenant: {e.message}", "danger")
            current_app.logger.error(f"Error updating tenant: {e.message}", exc_info=True)
            return render_template("update.html", form=form, tenant=tenant_data_before_update)
        except Exception as e:
            current_app.logger.exception(f"Unexpected error in process_update_tenant_form: {str(e)}")
            flash(f"An unexpected error occurred: {str(e)}", "danger")
            return render_template("update.html", form=form, tenant=tenant_data_before_update)
    else:
        flash("Please correct the errors in the form.", "danger")
        return render_template("update.html", form=form, tenant=tenant_data_before_update)
