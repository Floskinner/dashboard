class InvalidURL(Exception):
    def __init__(self, error_msg: str, url: str) -> None:
        super().__init__(error_msg)
        self.url = url
