import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import SQL
from flask.json import jsonify
from flask import Blueprint, request, make_response
import mysite.tokens as tokens
import Config
import pandas as pd


discord = Blueprint('discord', __name__, template_folder='templates')

@discord.route('/discord/locations/<token>', methods=['GET'])
def get_locations(token):

    verified = tokens.verify_token(token=token, verifcation='hiscores')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})

    # json = {'names':('ferrariic','extreme4all','seltzerbro')}
    players = request.get_json()

    if players is None:
        return jsonify({'Invalid Data':'Data'})

    players = players['names']
    data = SQL.get_player_report_locations(players)
    df = pd.DataFrame(data)
    output = df.to_dict('records')

    return jsonify(output)

@discord.route('/discord/region/<token>', methods=['GET'])
@discord.route('/discord/region/<token>/<regionName>', methods=['GET'])
def get_regions(token, regionName=None):

    verified = tokens.verify_token(token=token, verifcation='hiscores')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})
        
    if regionName is None:
        regionName = request.get_json()

        if regionName is None:
            return jsonify({'Invalid Data':'Data'})

        regionName = regionName['region']
    
    data = SQL.get_region_search(regionName)

    df = pd.DataFrame(data)
    output = df.to_dict('records')

    return jsonify(output)

@discord.route('/discord/heatmap/<token>', methods=['GET'])
@discord.route('/discord/heatmap/<token>/<region_id>', methods=['GET'])
def get_heatmap_data(token, region_id=None):

    verified = tokens.verify_token(token=token, verifcation='hiscores')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})
    if region_id is None:
        region_id = request.get_json()

        if region_id is None:
            return jsonify({'Invalid Data':'Data'})

        region_id = region_id['region_id']
    
    data = SQL.get_report_data_heatmap(region_id)

    df = pd.DataFrame(data)
    output = df.to_dict('records')

    return jsonify(output)

@discord.route('/discord/player_bans/<token>', methods=['GET'])
@discord.route('/discord/player_bans/<token>/<player_name>', methods=['GET'])
def get_player_bans(token, player_name=None):

    verified = tokens.verify_token(token=token, verifcation='hiscores')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})

    if player_name is None:
        player_name = request.get_json()
    
        if player_name is None:
            return jsonify({'Invalid Data':'Data'})

        player_name = player_name['player_name']
    
    data = SQL.get_player_banned_bots(player_name)

    df = pd.DataFrame(data)
    output = df.to_dict('records')

    return jsonify(output)
  

@discord.route('/discord/verify/player_rsn_discord_account_status/<token>/<player_name>', methods=['GET'])
def get_verification_status_information(token, player_name=None):

    verified = tokens.verify_token(token=token, verifcation='verify_players')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})

    if player_name is None:
        return jsonify({'Invalid Name':'Invalid Name'})
    
    data = SQL.get_verification_info(player_name)

    df = pd.DataFrame(data)
    output = df.to_dict('records')

    return jsonify(output)

@discord.route('/discord/verify/playerid/<token>/<player_name>', methods=['GET'])
def get_verification_playerid_information(token, player_name=None):

    verified = tokens.verify_token(token=token, verifcation='verify_players')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})

    if player_name is None:
        return jsonify({'Invalid Name':'Invalid Name'})
    
    data = SQL.get_verification_player_id(player_name)

    df = pd.DataFrame(data)
    output = df.to_dict('records')

    return jsonify(output)

@discord.route('/discord/verify/verified_player_info/<token>/<player_name>', methods=['GET'])
def get_verified_player_list_information(token, player_name=None):

    verified = tokens.verify_token(token=token, verifcation='verify_players')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})

    if player_name is None:
        return jsonify({'Invalid Name':'Invalid Name'})
    
    data = SQL.get_verified_info(player_name)

    df = pd.DataFrame(data)
    output = df.to_dict('records')

    return jsonify(output)

@discord.route('/discord/verify/insert_player_dpc/<token>/<discord_id>/<player_id>/<code>', methods=['POST', 'OPTIONS'])
def post_verified_insert_information(token, discord_id=None, player_id=None, code=None):

    #Preflight
    if request.method == 'OPTIONS':
        response = make_response()
        header = response.headers
        header['Access-Control-Allow-Origin'] = '*'
        return response

    verified = tokens.verify_token(token=token, verifcation='verify_players')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})

    if discord_id is None:
        return jsonify({'Invalid Discord':'Invalid Discord ID'})

    if player_id is None:
        return jsonify({'Invalid Player ID':'Invalid Player ID'})

    if code is None:
        return jsonify({'Invalid Code':'Invalid Code'})

    token_id = SQL.get_token(token).id
    
    data = SQL.verificationInsert(discord_id, player_id, code, token_id)

    return jsonify({'Value':f'{discord_id} {player_id} {code} Submitted'})


@discord.route('/discord/get_linked_accounts/<token>/<discord_id>', methods=['GET'])
def get_discord_linked_accounts(token, discord_id=None):

    verified = tokens.verify_token(token=token, verifcation='verify_players')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})

    if discord_id is None:
        return jsonify({'Invalid Name':'Invalid Name'})
    
    data = SQL.get_discord_linked_accounts(discord_id)

    df = pd.DataFrame(data)
    output = df.to_dict('records')

    return jsonify(output)

@discord.route('/discord/get_all_linked_ids/<token>', methods=['GET'])
def get_all_linked_ids(token):

    verified = tokens.verify_token(token=token, verifcation='verify_players')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})
    
    data = SQL.get_all_verified_ids()

    df = pd.DataFrame(data)
    output = df.to_dict('records')

    return jsonify(output)

'''
    Task routes
'''

@discord.route('/discord/slayer/get_slayer_labels/<token>', methods=['GET'])
def get_labels(token):

    verified = tokens.verify_token(token=token, verifcation='discord_general')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})
    
    data = SQL.get_label_names()

    df = pd.DataFrame(data)
    output = df.to_dict('records')

    return jsonify(output)

@discord.route('/discord/slayer/get_slayer_location/<token>/<label_name>', methods=['GET'])
def get_slayer_locations(token, label_name):

    verified = tokens.verify_token(token=token, verifcation='discord_general')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})
    
    data = SQL.get_botlabel_locations(label_name)

    df = pd.DataFrame(data)
    output = df.to_dict('records')

    return jsonify(output)

@discord.route('/discord/slayer/get-current-slayer-task/<token>/<playerName>', methods=['GET'])
def get_current_slayer_task(token, playerName):

    verified = tokens.verify_token(token=token, verifcation='discord_general')

    if not (verified):
        return jsonify({'Invalid Data':'Data'})
    
    data = SQL.get_slayer_profile(playerName)

    df = pd.DataFrame(data)
    output = df.to_dict('records')

    return jsonify(output)





    

