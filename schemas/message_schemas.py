from marshmallow import Schema, fields

class MessageSchema(Schema):
    """
    Schema for standardized API response messages.
    Used for success messages, and simple error messages.
    """
    status = fields.String(required=True)
    message = fields.String(required=True)
    code = fields.Integer()
    details = fields.Raw()

