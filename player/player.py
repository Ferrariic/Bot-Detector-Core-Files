import SQL
from flask import Blueprint
import models
import Config

player = Blueprint('player', __name__, template_folder='templates')

engine = Config.db_engines.get('playerdata')

#TODO: verify token, see auth.py
#TODO: decorator for token verification
'''
    Tokens with extra verification on token
'''
def verify_token(token, verifcation):
    player_token = SQL.get_token(token)

    if not (player_token):
        return False

    if verifcation == "hiscores":
        if not (player_token.request_highscores == 1):
            return False

    if verifcation == "ban":
        if not (player_token.verify_ban == 1):
            return False

    if verifcation == "create_token":
        if not (player_token.create_token == 1):
            return False

    if verifcation == "verify_players":
        if not (player_token.verify_players == 1):
            return False

    return True


@player.route('<version>/player/<token>', methods=['GET'])
def get_player(version=None, token=None):
    if not (verify_token(token, verifcation='hiscore')):
        return "<h1>404</h1><p>Invalid token</p>", 404
    pass

@player.route('<version>/player/<token>', methods=['POST'])
def update_player(version=None, token=None):
    if not (verify_token(token, verifcation='ban')):
        return "<h1>404</h1><p>Invalid token</p>", 404
    pass
