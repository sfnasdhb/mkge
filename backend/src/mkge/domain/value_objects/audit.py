"""Audit action enum — all auditable events in the system."""
from enum import Enum


class AuditAction(str, Enum):
    USER_REGISTER = "USER_REGISTER"
    USER_LOGIN = "USER_LOGIN"
    UPLOAD_DOCUMENT = "UPLOAD_DOCUMENT"
    DELETE_DOCUMENT = "DELETE_DOCUMENT"
    QUERY_GRAPHRAG = "QUERY_GRAPHRAG"
    ADMIN_UPDATE_USER = "ADMIN_UPDATE_USER"
    ADMIN_DELETE_USER = "ADMIN_DELETE_USER"
