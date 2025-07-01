
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from forms import BranchForm

from services.branch_service import branch_service
from services.country_service import country_service
from services.tenant_service import tenant_service 


from errors import ValidationError, DuplicateBranchCodeError, NotFoundError, ApplicationError

branch_web_bp = Blueprint('web_branch', __name__)

@branch_web_bp.route('/branches/view/<int:tenant_id>')
def view_branches(tenant_id):
    """
    Web route to view all branches for a specific tenant.
    """
    try:
        
        tenant_service.get_tenant_by_id(tenant_id) 
        branches = branch_service.get_branches_by_tenant(tenant_id) 
        return render_template('view_branch.html', branches=branches, tenant_id=tenant_id)
    except NotFoundError as e:
        flash(f"Tenant not found: {e.message}. Cannot view branches.", "danger")
        return redirect(url_for('web_general.index_get'))
    except ApplicationError as e:
        flash(f"Error loading branches: {e.message}", "danger")
        current_app.logger.error(f"Error loading branches for tenant {tenant_id}: {e.message}", exc_info=True)
        return redirect(url_for('web_general.index_get'))
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        current_app.logger.exception(f"Unexpected error in view_branches for tenant {tenant_id}: {e}")
        return redirect(url_for('web_general.index_get'))


@branch_web_bp.route('/branches/<int:branch_id>/edit', methods=["GET"])
def show_edit_branch_form(branch_id):
    """
    Displays the form to update an existing branch.
    """
    try:
        branch = branch_service.get_branch_by_id(branch_id)
        
        class DictAsObj:
            def __init__(self, dictionary):
                for key, value in dictionary.items():
                    setattr(self, key, value)
        branch_obj = DictAsObj(branch)

        form = BranchForm(obj=branch_obj)

        countries = country_service.get_all_countries()
        form.country_id.choices = [(c['country_id'], c['country_name']) for c in countries]
        form.country_id.data = branch.get('country_id') 

        return render_template('update_branch.html', form=form, form_title='Update Branch')
    except NotFoundError as e:
        flash(f"Branch not found: {e.message}", "danger")
        return redirect(url_for('web_general.index_get'))
    except ApplicationError as e:
        flash(f"Error loading branch for update: {e.message}", "danger")
        current_app.logger.error(f"Error loading branch for update form (ID {branch_id}): {e.message}", exc_info=True)
        return redirect(url_for('web_general.index_get'))
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in show_edit_branch_form (ID {branch_id}): {str(e)}")
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        return redirect(url_for('web_general.index_get'))


@branch_web_bp.route('/branches/<int:branch_id>/edit', methods=["POST"])
def process_edit_branch_form(branch_id):
    """
    Processes the submission of the branch update form.
    """
    
    branch_data_before_update = None
    try:
        branch_data_before_update = branch_service.get_branch_by_id(branch_id)
    except NotFoundError as e:
        flash(f"Branch not found: {e.message}", "danger")
        return redirect(url_for('web_general.index_get'))
    except ApplicationError as e:
        flash(f"Error loading branch for update: {e.message}", "danger")
        current_app.logger.error(f"Error loading branch for update form (POST, ID {branch_id}): {e.message}", exc_info=True)
        return redirect(url_for('web_general.index_get'))
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in process_edit_branch_form (pre-load, ID {branch_id}): {str(e)}")
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        return redirect(url_for('web_general.index_get'))


    form = BranchForm(request.form)
    try:
        countries = country_service.get_all_countries()
        form.country_id.choices = [(c['country_id'], c['country_name']) for c in countries]
    except ApplicationError as e:
        flash(f"Error loading countries: {e.message}", "danger")
        current_app.logger.error(f"Error loading countries for branch form (POST, ID {branch_id}): {e.message}", exc_info=True)
        form.country_id.choices = []

    if form.validate_on_submit():
        update_data = {
            'name': form.name.data,
            'description': form.description.data,
            'status': form.status.data,
            'code': form.code.data,
            'country_id': form.country_id.data,
            'tenant_id': branch_data_before_update['tenant_id'] 
        }
        try:
            updated_branch = branch_service.update_branch(branch_id, update_data)
            flash(f"Branch '{updated_branch['name']}' updated successfully!", "success")
            return redirect(url_for('web_general.index_get'))
        except (ValidationError, DuplicateBranchCodeError, NotFoundError, ApplicationError) as e:
            flash(f"Error updating branch: {e.message}", "danger")
            current_app.logger.error(f"Error updating branch ID {branch_id}: {e.message}", exc_info=True)
            return render_template('update_branch.html', form=form, form_title='Update Branch')
        except Exception as e:
            current_app.logger.exception(f"Unexpected error during branch update (ID: {branch_id}): {str(e)}")
            flash(f"An unexpected error occurred: {str(e)}", "danger")
            return render_template('update_branch.html', form=form, form_title='Update Branch')
    else:
        flash("Please fix the errors in the form.", "danger")
        return render_template('update_branch.html', form=form, form_title='Update Branch')


@branch_web_bp.route('/branches/create/<int:tenant_id>', methods=["GET"])
def show_branch_creation_form(tenant_id):
    """
    Web route to display the form for creating a new branch under a specific tenant.
    """
    form = BranchForm()
    form.tenant_id.data = tenant_id 
    try:
        countries = country_service.get_all_countries()
        form.country_id.choices = [(c['country_id'], c['country_name']) for c in countries]
    except ApplicationError as e:
        flash(f"Error loading countries: {e.message}", "danger")
        current_app.logger.error(f"Error loading countries for branch form: {e.message}", exc_info=True)
        form.country_id.choices = []
    return render_template('add_branch.html', form=form, tenant_id=tenant_id, form_title='Add Branch')

@branch_web_bp.route('/branches/create/<int:tenant_id>', methods=["POST"])
def create_branch(tenant_id):
    """
    Web route to handle submission of the branch creation form.
    """
    form = BranchForm()
    form.tenant_id.data = tenant_id
    try:
        countries = country_service.get_all_countries()
        form.country_id.choices = [(c['country_id'], c['country_name']) for c in countries]
    except ApplicationError as e:
        flash(f"Error loading countries: {e.message}", "danger")
        current_app.logger.error(f"Error loading countries for branch form (POST): {e.message}", exc_info=True)
        form.country_id.choices = []

    if form.validate_on_submit():
        branch_data = {
            'name': form.name.data,
            'description': form.description.data,
            'status': form.status.data,
            'code': form.code.data,
            'country_id': form.country_id.data,
            'tenant_id': tenant_id
        }
        try:
            new_branch = branch_service.create_branch(tenant_id, branch_data)
            flash(f"Branch '{new_branch['name']}' created successfully!", "success")
            return redirect(url_for('web_general.index_get'))
        except (ValidationError, DuplicateBranchCodeError, NotFoundError, ApplicationError) as e:
            flash(f"Error creating branch: {e.message}", "danger")
            current_app.logger.error(f"Error creating branch for tenant {tenant_id}: {e.message}", exc_info=True)
            return render_template('add_branch.html', form=form, tenant_id=tenant_id, form_title='Add Branch')
        except Exception as e:
            current_app.logger.exception(f"Unexpected error during branch creation for tenant {tenant_id}: {str(e)}")
            flash(f"An unexpected error occurred: {str(e)}", "danger")
            return render_template('add_branch.html', form=form, tenant_id=tenant_id, form_title='Add Branch')
    return render_template('add_branch.html', form=form, tenant_id=tenant_id, form_title='Add Branch')