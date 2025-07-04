
class ApplicationError(Exception):
    """Base class for custom application-specific errors."""
    def __init__(self, message="An application error occurred", status_code=500, errors=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors 

class DatabaseOperationError(ApplicationError):
    """Error raised for general database operation failures."""
    def __init__(self, message="A database operation failed."):
        super().__init__(message, status_code=500)

class ValidationError(ApplicationError):
    """Error raised for invalid input data."""
    def __init__(self, message="Invalid data provided.", errors=None):
        super().__init__(message, status_code=400, errors=errors)

class NotFoundError(ApplicationError):
    """Base error raised when a requested resource is not found."""
    def __init__(self, message="Resource not found."):
        super().__init__(message, status_code=404)

class TenantNotFoundError(NotFoundError):
    """Error raised when a Tenant resource is not found."""
    def __init__(self, message="Tenant not found."):
        super().__init__(message)

class BranchNotFoundError(NotFoundError):
    """Error raised when a Branch resource is not found."""
    def __init__(self, message="Branch not found."):
        super().__init__(message)

class ProductNotFoundError(NotFoundError):
    """Error raised when a Product resource is not found."""
    def __init__(self, message="Product not found."):
        super().__init__(message)

class ModuleNotFoundError(NotFoundError):
    """Error raised when a Module resource is not found."""
    def __init__(self, message="Module not found."):
        super().__init__(message)

class ProductModuleNotFoundError(NotFoundError):
    """Error raised when a ProductModule resource is not found."""
    def __init__(self, message="Product Module not found."):
        super().__init__(message)

class FeatureNotFoundError(NotFoundError):
    """Error raised when a Feature resource is not found."""
    def __init__(self, message="Feature not found."):
        super().__init__(message)

class TenantFeatureNotFoundError(NotFoundError):
    """Error raised when a TenantFeature resource is not found."""
    def __init__(self, message="Tenant Feature not found."):
        super().__init__(message)

class ProductTagNotFoundError(NotFoundError):
    """Error raised when a ProductTag resource is not found."""
    def __init__(self, message="Product Tag not found."):
        super().__init__(message)


class DuplicateError(ApplicationError):
    """Base error raised for duplicate entries where unique constraint is violated."""
    def __init__(self, message="A duplicate entry already exists.", field=None):
        super().__init__(message, status_code=409)
        self.field = field

class DuplicateOrganizationCodeError(DuplicateError):
    def __init__(self, message="Organization code already exists."):
        super().__init__(message, field="organization_code")

class DuplicateSubDomainError(DuplicateError):
    def __init__(self, message="Sub-domain already exists."):
        super().__init__(message, field="sub_domain")

class DuplicateBranchCodeError(DuplicateError):
    def __init__(self, message="Branch code already exists."):
        super().__init__(message, field="code")

class DuplicateProductCodeError(DuplicateError):
    def __init__(self, message="Product code already exists."):
        super().__init__(message, field="code")

class DuplicateModuleConfigurationError(DuplicateError):
    def __init__(self, message="This module is already configured for this branch and product."):
        super().__init__(message, field="product_module")

class DuplicateTenantFeatureError(DuplicateError):
    def __init__(self, message="This feature is already configured for this tenant."):
        super().__init__(message, field="tenant_feature")

class DuplicateTenantReportError(DuplicateError):
    def __init__(self, message="This report is already configured for this tenant."):
        super().__init__(message, field="tenant_report")
