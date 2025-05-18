import logging
import time
from typing import Annotated
from fastapi import Header, HTTPException, Cookie

LOGGER = logging.getLogger("playlist")

# TODO: finalize permission model and actually do auth
class Authenticate:
    def __init__(self, permission_level: int):
        self.permission_level = permission_level
    
    def __call__(
        self,
        authorization_header: Annotated[str, Header()]=None,
        authorization_cookie: Annotated[str|None, Cookie()]=None
    ) -> dict:
        time_auth_start = time.perf_counter()
        if authorization_header:
            LOGGER.debug("authorization_header header found!")
            # user_info = self.validateToken(authorization_header)
        elif authorization_cookie:
            LOGGER.debug("authorization_cookie found!")
            # user_info = self.validateToken(authorization_cookie)
        else:
            pass
            # raise HTTPException(status_code=401, detail="Unauthorized")
        # return user_info
        LOGGER.info(f"Auth took {time.perf_counter() - time_auth_start}s!")
        return {"id": 123, "name": "abcde"}
