from marshmallow import Schema, fields, validate

class ConfiguredBranchProductModuleOutputSchema(Schema):
    """
    Specific schema for the API endpoint that shows modules configured for a branch and product.
    This mimics the exact output structure requested in the original app.py.
    """
    branch_id = fields.Integer(required=True)
    product_id = fields.Integer(required=True)
    module_id = fields.Integer(required=True)
    module_name = fields.String(required=True)

class AvailableProductModuleOutputSchema(Schema):
    """
    Specific schema for the API endpoint that shows available modules for a product,
    including whether they are configured for a given branch.
    """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    is_configured = fields.Boolean(required=True)

