from loguru import logger

from .auth import User, get_current_user

from fastapi import Depends, HTTPException, status


class RequiredScopes:
    """Check if user is authorized to access endpoint. Check based on scopes.

    Parameters
    ----------
    required_scopes : list[str]
        list of strings specifying the scope required to access endpoint.

    Returns
    -------
    bool
        If user has all the required scopes, True is returned. Otherwise exception is
        raised.

    Raises
    ------
    HTTPException
        If user does not have the required scopes

    """

    def __init__(self, required_scopes: list[str]) -> None:
        self.required_scopes = required_scopes

    def __call__(self, user: User = Depends(get_current_user)) -> bool:
        missing_permissions = [
            permission
            for permission in self.required_scopes
            if permission not in user.scopes
        ]

        if missing_permissions:
            missing_permissions_str = ", ".join(missing_permissions)
            logger.warning(
                f"Unauthorized access attempt by user '{user.username}' ({user.user_id}) to protected endpoint "
                f"without required permission(s): {missing_permissions_str}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Scopes"},
            )
        return True
