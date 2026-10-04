class CityCareError(Exception):
    pass


class WardFullError(CityCareError):
    pass


class ClaimRejectedError(CityCareError):
    pass


class ResourceConflictError(CityCareError):
    pass


class InvalidOperationError(CityCareError):
    pass


class InvalidTransitionError(CityCareError):
    pass


class AllergyAlertError(CityCareError):
    pass


class DrugInteractionError(CityCareError):
    pass


class NurseCoverageError(CityCareError):
    pass


class BloodUnavailableError(CityCareError):
    pass


class VisitorPolicyError(CityCareError):
    pass


class OutOfStockError(CityCareError):
    pass
