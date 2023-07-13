from database.psql import Database
from function.api import update_tokens


async def token():
    db = Database()
    tokens = db.get_token()
    link = 'https://auth.dodois.io/connect/token'
    token_response = await update_tokens(url=link, refresh=tokens[1])
    access = token_response['access_token']
    refresh = token_response['refresh_token']
    db.update_token(tokens[0], access, refresh)
