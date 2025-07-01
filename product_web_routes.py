
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from forms import ProductForm

from services.product_services import product_service
from services.product_tag_service import product_tag_service


from errors import ValidationError, DuplicateProductCodeError, NotFoundError, ApplicationError

product_web_bp = Blueprint('web_product', __name__)

@product_web_bp.route('/products/view')
def view_all_products():
    """
    Web route to view all products.
    """
    try:
        products = product_service.get_all_products() 
        return render_template('view_product.html', products=products)
    except ApplicationError as e:
        flash(f"Error loading products: {e.message}", "danger")
        current_app.logger.error(f"Error in view_all_products: {e.message}", exc_info=True)
        return render_template('view_product.html', products=[])
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        current_app.logger.exception(f"Unexpected error in view_all_products: {e}")
        return render_template('view_product.html', products=[])


@product_web_bp.route("/products/create", methods=["GET"])
def show_create_product_form():
    """
    Web route to display the form for creating a new product.
    """
    form = ProductForm()
    try:
        
        parent_products = product_service.get_all_products(minimal=True) 
        form.parent_product_id.choices = [(0, '-- None --')] + [(p['product_id'], p['name']) for p in parent_products]
        product_tags = product_tag_service.get_all_product_tags()
        form.product_tag_id.choices = [(0, '-- None --')] + [(pt['product_tag_id'], pt['name']) for pt in product_tags]
    except ApplicationError as e:
        flash(f"Error loading dropdown data: {e.message}", "danger")
        current_app.logger.error(f"Error loading dropdowns for product form: {e.message}", exc_info=True)
        form.parent_product_id.choices = [(0, '-- None --')]
        form.product_tag_id.choices = [(0, '-- None --')]
    return render_template("add_product.html", form=form, form_title="Add Product")


@product_web_bp.route("/products/create", methods=["POST"])
def create_product():
    """
    Web route to handle submission of the product creation form.
    """
    form = ProductForm()
    try:
        parent_products = product_service.get_all_products(minimal=True)
        form.parent_product_id.choices = [(0, '-- None --')] + [(p['product_id'], p['name']) for p in parent_products]
        product_tags = product_tag_service.get_all_product_tags()
        form.product_tag_id.choices = [(0, '-- None --')] + [(pt['product_tag_id'], pt['name']) for pt in product_tags]
    except ApplicationError as e:
        flash(f"Error loading dropdown data: {e.message}", "danger")
        current_app.logger.error(f"Error loading dropdowns for product form (POST): {e.message}", exc_info=True)
        form.parent_product_id.choices = [(0, '-- None --')]
        form.product_tag_id.choices = [(0, '-- None --')]

    if form.validate_on_submit():
        product_data = {
            'name': form.name.data,
            'code': form.code.data,
            'description': form.description.data,
            'tag': form.tag.data,
            'sequence': form.sequence.data,
            'parent_product_id': form.parent_product_id.data if form.parent_product_id.data != 0 else None,
            'is_inbound': form.is_inbound.data,
            'product_tag_id': form.product_tag_id.data if form.product_tag_id.data != 0 else None,
            'supported_file_formats': form.supported_file_formats.data
        }
        try:
            new_product = product_service.create_product(product_data)
            flash(f"Product '{new_product['name']}' created successfully!", "success")
            return redirect(url_for('web_root.web_general.index_get'))
        except (ValidationError, DuplicateProductCodeError, ApplicationError) as e:
            flash(f"Error creating product: {e.message}", "danger")
            current_app.logger.error(f"Error creating product: {e.message}", exc_info=True)
            return render_template("add_product.html", form=form, form_title="Add Product")
        except Exception as e:
            current_app.logger.exception(f"Unexpected error in create_product POST: {str(e)}")
            flash(f"An unexpected error occurred: {str(e)}", "danger")
            return render_template("add_product.html", form=form, form_title="Add Product")
    return render_template("add_product.html", form=form, form_title="Add Product")

@product_web_bp.route("/products/<int:product_id>/edit", methods=["GET"])
def show_update_product_form(product_id):
    """
    Displays the form to update an existing product.
    """
    try:
        product = product_service.get_product_by_id(product_id)
        
        class DictAsObj:
            def __init__(self, dictionary):
                for key, value in dictionary.items():
                    setattr(self, key, value)
        product_obj = DictAsObj(product)
        form = ProductForm(obj=product_obj)

        parent_products = product_service.get_all_products(minimal=True)
        form.parent_product_id.choices = [(0, '-- None --')] + \
                                         [(p['product_id'], p['name']) for p in parent_products if p['product_id'] != product_id]
        product_tags = product_tag_service.get_all_product_tags()
        form.product_tag_id.choices = [(0, '-- None --')] + \
                                      [(pt['product_tag_id'], pt['name']) for pt in product_tags]

        form.parent_product_id.data = product.get('parent_product_id') or 0
        form.product_tag_id.data = product.get('product_tag_id') or 0
        return render_template("update_product.html", form=form, form_title="Update Product")
    except NotFoundError as e:
        flash(f"Product not found: {e.message}", "danger")
        return redirect(url_for('web_root.web_general.index_get'))
    except ApplicationError as e:
        flash(f"Error loading product for update: {e.message}", "danger")
        current_app.logger.error(f"Error loading product for update form (ID {product_id}): {e.message}", exc_info=True)
        return redirect(url_for('web_root.web_general.index_get'))
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in show_update_product_form (ID {product_id}): {str(e)}")
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        return redirect(url_for('web_root.web_general.index_get'))


@product_web_bp.route("/products/<int:product_id>/edit", methods=["POST"])
def process_update_product_form(product_id):
    """
    Processes the submission of the product update form.
    """
   
    product_data_before_update = None
    try:
        product_data_before_update = product_service.get_product_by_id(product_id)
    except NotFoundError as e:
        flash(f"Product not found: {e.message}", "danger")
        return redirect(url_for('web_root.web_general.index_get'))
    except ApplicationError as e:
        flash(f"Error loading product for update: {e.message}", "danger")
        current_app.logger.error(f"Error loading product for update form (POST, ID {product_id}): {e.message}", exc_info=True)
        return redirect(url_for('web_root.web_general.index_get'))
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in process_update_product_form (pre-load, ID {product_id}): {str(e)}")
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        return redirect(url_for('web_root.web_general.index_get'))

    form = ProductForm(request.form)
    parent_products = product_service.get_all_products(minimal=True)
    form.parent_product_id.choices = [(0, '-- None --')] + \
                                     [(p['product_id'], p['name']) for p in parent_products if p['product_id'] != product_id]
    product_tags = product_tag_service.get_all_product_tags()
    form.product_tag_id.choices = [(0, '-- None --')] + \
                                  [(pt['product_tag_id'], pt['name']) for pt in product_tags]

    if form.validate():
        update_data = {
            'name': form.name.data,
            'code': form.code.data,
            'description': form.description.data,
            'tag': form.tag.data,
            'sequence': form.sequence.data,
            'parent_product_id': form.parent_product_id.data if form.parent_product_id.data != 0 else None,
            'is_inbound': form.is_inbound.data,
            'product_tag_id': form.product_tag_id.data if form.product_tag_id.data != 0 else None,
            'supported_file_formats': form.supported_file_formats.data
        }
        try:
            updated_product = product_service.update_product(product_id, update_data)
            flash(f"Product '{updated_product['name']}' updated successfully!", "success")
            return redirect(url_for('web_root.web_general.index_get'))
        except (ValidationError, DuplicateProductCodeError, NotFoundError, ApplicationError) as e:
            flash(f"Error updating product: {e.message}", "danger")
            current_app.logger.error(f"Error updating product ID {product_id}: {e.message}", exc_info=True)
            return render_template("update_product.html", form=form, form_title="Update Product")
        except Exception as e:
            current_app.logger.exception(f"Unexpected error during product update (ID: {product_id}): {str(e)}")
            flash(f"An unexpected error occurred: {str(e)}", "danger")
            return render_template("update_product.html", form=form, form_title="Update Product")
    else:
        flash("Please fix the errors in the form.", "danger")
        return render_template("update_product.html", form=form, form_title="Update Product")