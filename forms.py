from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, SubmitField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class TenantForm(FlaskForm):
    organization_code = StringField(
        'Organization Code', 
        validators=[DataRequired(), Length(max=50)]
    )

    tenant_name = StringField(
        'Tenant Name', 
        validators=[Optional(), Length(max=100)]
    )

    sub_domain = StringField(
        'Subdomain', 
        validators=[DataRequired(), Length(max=50)]
    )

    default_currency = StringField(
        'Default Currency', 
        validators=[DataRequired(), Length(max=3)], 
        default='USD'
    )

    description = TextAreaField(
        'Description', 
        validators=[Optional(), Length(max=500)]
    )

    status = SelectField(
        'Status', 
        choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
        default='Active'
    )

    country_id = SelectField(
        'Country',
        coerce=int,
        validators=[DataRequired()]
    )
    submit = SubmitField('Save')


class BranchForm(FlaskForm):
    tenant_id = HiddenField('Tenant ID', validators=[DataRequired()])

    name = StringField(
        'Branch Name',
        validators=[DataRequired(), Length(max=50)]
    )

    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=500)]
    )

    status = SelectField(
        'Status',
        choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
        default='Active',
        validators=[DataRequired()]
    )

    code = StringField(
        'Branch Code',
        validators=[Optional(), Length(max=50)]
    )

    country_id = SelectField(
        'Country',
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField('Save')
    
class ModuleForm(FlaskForm): 

    name = StringField(
        'Module Name',
        validators=[DataRequired(), Length(max=50)]
    )

    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=255)]
    )

    code = StringField(
        'Module Code',
        validators=[Optional(), Length(max=50)]
    )

    dependent_modules = TextAreaField('Dependent Modules (JSON)', validators=[Optional()])

    submit = SubmitField('Save')
    
class ProductForm(FlaskForm):
    name = StringField(
        'Product Name',
        validators=[DataRequired(), Length(max=50)]
    )
    
    code = StringField(
        'Product Code',
        validators=[Optional(), Length(max=50)]
    )
    
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=500)]
    )
    
    tag = StringField(
        'Tag',
        validators=[Optional(), Length(max=50)]
    )
    
    sequence = IntegerField(
        'Sequence',
        validators=[Optional(), NumberRange(min=0)],
        default=0
    )
    
    parent_product_id = SelectField(
        'Parent Product',
        coerce=int,
        validators=[Optional()]
    )
    
    is_inbound = BooleanField('Is Inbound')
    
    product_tag_id = SelectField(
        'Product Tag',
        coerce=int,
        validators=[Optional()]
    )
    
    supported_file_formats = StringField(
        'Supported File Formats',
        validators=[Optional(), Length(max=250)],
        description='Comma separated formats (e.g. pdf, docx, jpg)'
    )
    
    submit = SubmitField('Save')
    
class ProductModuleForm(FlaskForm):
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    module_id = HiddenField('Module ID', validators=[DataRequired()])

    name = StringField(
        'Name',
        validators=[DataRequired(), Length(max=50)]
    )

    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=500)]
    )

    status = SelectField(
        'Status',
        choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
        default='Active',
        validators=[DataRequired()]
    )

    code = StringField(
        'Code',
        validators=[Optional(), Length(max=50)]
    )

    submit = SubmitField('Save')
