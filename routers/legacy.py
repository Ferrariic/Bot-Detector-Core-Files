import logging
import time
from typing import List

import Config
import pandas as pd
import SQL
from database.functions import execute_sql, list_to_string
from fastapi import APIRouter
from pydantic import BaseModel

'''
This file will have all legacy routes from the Flask api.
after everything is ported, validated & discussed route desing should be done
'''

router = APIRouter()

class contributor(BaseModel):
    name: str

class equipment(BaseModel):
    equip_head_id: int
    equip_amulet_id: int
    equip_torso_id: int
    equip_legs_id: int
    equip_boots_id: int
    equip_cape_id: int
    equip_hands_id: int
    equip_weapon_id: int
    equip_shield_id: int

class detection(BaseModel):
    reporter: str
    reported: str
    region_id: int
    x_coord: int
    y_coord: int
    z_coord: int
    ts: int
    manual_detect: int
    on_members_world: int
    on_pvp_world: int
    world_number: int
    equipment: equipment
    equip_ge_value: int

async def sql_get_player(player_name):
    sql_player_id = 'select * from Players where name = :player_name;'

    param = {
        'player_name': player_name
    }

    # returns a list of players
    player = await execute_sql(sql_player_id, param=param, debug=False)
    player = player.rows2dict()

    player_id = None if len(player) == 0 else player[0]

    return player_id

async def sql_insert_player(player_name):
    sql_insert = "insert ignore into Players (name) values(:player_name);"

    param = {
        'player_name': player_name
    }

    await execute_sql(sql_insert, param=param, debug=False)
    player = await sql_get_player(player_name)
    return player

async def sql_insert_report(data):
    gmt = time.gmtime(data['ts'])
    human_time = time.strftime('%Y-%m-%d %H:%M:%S', gmt)

    param = {
        'reportedID': data.get('reported'),
        'reportingID': data.get('reporter'),
        'region_id': data.get('region_id'),
        'x_coord': data.get('x'),
        'y_coord': data.get('y'),
        'z_coord': data.get('z'),
        'timestamp': human_time,
        'manual_detect': data.get('manual_detect'),
        'on_members_world': data.get('on_members_world'),
        'on_pvp_world': data.get('on_pvp_world'),
        'world_number': data.get('world_number'),
        'equip_head_id': data.get('equipment').get('HEAD'),
        'equip_amulet_id': data.get('equipment').get('AMULET'),
        'equip_torso_id': data.get('equipment').get('TORSO'),
        'equip_legs_id': data.get('equipment').get('LEGS'),
        'equip_boots_id': data.get('equipment').get('BOOTS'),
        'equip_cape_id': data.get('equipment').get('CAPE'),
        'equip_hands_id': data.get('equipment').get('HANDS'),
        'equip_weapon_id': data.get('equipment').get('WEAPON'),
        'equip_shield_id': data.get('equipment').get('SHIELD'),
        'equip_ge_value': data.get('equipment_ge')
    }

    # list of column values
    columns = list_to_string(list(param.keys()))
    values = list_to_string([f':{column}' for column in list(param.keys())])

    sql = f'insert ignore into Reports ({columns}) values ({values});'
    await execute_sql(sql, param=param, debug=False)
    return

async def sql_get_contributions(contributors):
    query = '''
        SELECT
            rs.detect,
            rs.reported as reported_ids,
            pl.confirmed_ban as confirmed_ban,
            pl.possible_ban as possible_ban,
            pl.confirmed_player as confirmed_player
        FROM
            (SELECT
                r.reportedID as reported,
                r.manual_detect as detect
        FROM Reports as r
        JOIN Players as pl on pl.id = r.reportingID
        WHERE 1=1
            AND pl.name IN :contributors ) rs
        JOIN Players as pl on (pl.id = rs.reported);
    '''

    params = {
        "contributors": contributors
    }

    data = await execute_sql(query, param=params, debug=False)
    return data.rows2dict()

async def name_check(name):
    bad_name = False
    if len(name) > 13:
        bad_name = True

    temp_name = name
    temp_name = temp_name.replace(' ', '')
    temp_name = temp_name.replace('_', '')
    temp_name = temp_name.replace('-', '')

    if not (temp_name.isalnum()):
        bad_name = True

    return name, bad_name

async def custom_hiscore(detection):
    # input validation
    bad_name = False
    detection['reporter'], bad_name = name_check(detection['reporter'])
    detection['reported'], bad_name = name_check(detection['reported'])

    if bad_name:
        Config.debug(
            f"bad name: reporter: {detection['reporter']} reported: {detection['reported']}")
        return 0

    if not (0 <= int(detection['region_id']) <= 15522):
        return 0

    if not (0 <= int(detection['region_id']) <= 15522):
        return 0

    # get reporter & reported
    reporter = await sql_get_player(detection['reporter'])
    reported = await sql_get_player(detection['reported'])

    create = 0
    # if reporter or reported is None (=player does not exist), create player
    if reporter is None:
        reporter = await sql_insert_player(detection['reporter'])
        create += 1

    if reported is None:
        reported = await sql_insert_player(detection['reported'])
        create += 1

    # change in detection
    detection['reported'] = int(reported.id)
    detection['reporter'] = int(reporter.id)

    # insert into reports
    await sql_insert_report(detection)
    return create

async def insync_detect(detections, manual_detect):
    total_creates = 0
    for idx, detection in enumerate(detections):
        detection['manual_detect'] = manual_detect

        total_creates += await custom_hiscore(detection)

        if len(detection) > 1000 and total_creates/len(detections) > .75:
            logging.debug(f'    Malicious: sender: {detection["reporter"]}')
            break

        if idx % 500 == 0 and idx != 0:
            logging.debug(f'      Completed {idx + 1}/{len(detections)}')

    logging.debug(f'      Done: Completed {idx + 1} detections')
    return

@router.post('/{version}/plugin/detect/{manual_detect}', tags=['legacy'])
async def post_detect(detections: List[detection], version: str = None, manual_detect: int = 0):
    manual_detect = 0 if int(manual_detect) == 0 else 1

    # remove duplicates
    df = pd.DataFrame([d.__dict__ for d in detections])
    df.drop_duplicates(subset=['reporter', 'reported', 'region_id'], inplace=True)

    if len(df) > 5000 or df["reporter"].nunique() > 1:
        logging.debug('to many reports')
        return {'NOK': 'NOK'}, 400

    detections = df.to_dict('records')

    logging.debug(f'      Received detections: DF shape: {df.shape}')
    # Config.sched.add_job(insync_detect, args=[detections, manual_detect], replace_existing=False, name='detect')
    return {'OK': 'OK'}

async def parse_contributors(contributors: list, version:str=None) -> dict:
    contributions = await sql_get_contributions(contributors)
    
    df = pd.DataFrame(contributions)
    df = df.drop_duplicates(inplace=False, subset=["reported_ids", "detect"], keep="last")

    try:
        df_detect_manual = df.loc[df['detect'] == 1]

        manual_dict = {
            "reports": len(df_detect_manual.index),
            "bans": int(df_detect_manual['confirmed_ban'].sum()),
            "possible_bans": int(df_detect_manual['possible_ban'].sum()),
            "incorrect_reports": int(df_detect_manual['confirmed_player'].sum())
        }
    except KeyError:
        manual_dict = {
            "reports": 0,
            "bans": 0,
            "possible_bans": 0,
            "incorrect_reports": 0
        }

    try:
        df_detect_passive = df.loc[df['detect'] == 0]

        passive_dict = {
            "reports": len(df_detect_passive.index),
            "bans": int(df_detect_passive['confirmed_ban'].sum()),
            "possible_bans": int(df_detect_passive['possible_ban'].sum())
        }
    except KeyError:
        passive_dict = {
            "reports": 0,
            "bans": 0,
            "possible_bans": 0
        }

    total_dict = {
        "reports": passive_dict['reports'] + manual_dict['reports'],
        "bans": passive_dict['bans'] + manual_dict['bans'],
        "possible_bans": passive_dict['possible_bans'] + manual_dict['possible_bans']
    }

    if version in ['1.3','1.3.1'] or None:
        return total_dict

    return_dict = {
        "passive": passive_dict,
        "manual": manual_dict,
        "total": total_dict
    }

    return return_dict

@router.post('/stats/contributions/', tags=['legacy'])
async def get_contributions(contributors: List[contributor]):
    contributors = [d.__dict__["name"] for d in contributors]
    
    data = await parse_contributors(contributors, version=None)
    return data

@router.get('/{version}/stats/contributions/{contributor}', tags=['legacy'])
async def get_contributions(contributors: str, version: str):
    data = await parse_contributors([contributors], version=version)
    return data


@router.get('/stats/getcontributorid/{contributor}', tags=['legacy'])
async def get_contributor_id(contributor: str):
    player = await sql_get_player(contributor)

    if player:
        return_dict = {
            "id": player.id
        }

    return return_dict
