from starlette_admin.exceptions import LoginFailed



class AccessFailed(LoginFailed):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self.msg = msg