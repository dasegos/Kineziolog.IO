class InvalidStatusPassedError(Exception):
    async def __str__(self) -> str:
        return 'Unknown status passed - possible statuses are `member`, `blocked`'

class UnknownAuthLevel(Exception):
    '''Unknown authentication level for `AutheticationMiddleware()`'''
    def __init__(self, level: int) -> None:
        self.level = level

    def __str__(self):
        return f'{self.level} - Unknown authentication level! Accessible levels: 0, 1'