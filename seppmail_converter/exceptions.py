from click import ClickException


class AuthenticationError(ClickException):
    pass


class ExportError(ClickException):
    pass
