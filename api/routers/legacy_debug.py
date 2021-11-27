import asyncio
import re
from typing import List, Optional

import pandas as pd
from api.Config import app
from api.database.functions import execute_sql, list_to_string, verify_token
from fastapi import APIRouter
from pydantic import BaseModel
import time
import logging
logger = logging.getLogger(__name__)

router = APIRouter()

async def run_in_process(fn, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(app.state.executor, fn, *args)

'''DETECT ROUTE'''
class equipment(BaseModel):
    equip_head_id: Optional[int]
    equip_amulet_id: Optional[int]
    equip_torso_id: Optional[int]
    equip_legs_id: Optional[int]
    equip_boots_id: Optional[int]
    equip_cape_id: Optional[int]
    equip_hands_id: Optional[int]
    equip_weapon_id: Optional[int]
    equip_shield_id: Optional[int]

class detection(BaseModel):
    reporter: str
    reported: str
    region_id: int
    x: int
    y: int
    z: int
    ts: int
    on_members_world: int
    on_pvp_world: int
    world_number: int
    equipment: Optional[equipment]
    equip_ge_value: Optional[int]

async def is_valid_rsn(rsn: str) -> bool:
    return re.fullmatch('[\w\d\s_-]{1,13}', rsn)

async def to_jagex_name(name: str) -> str:
    return name.lower().replace('_', ' ').replace('-',' ').strip()

async def sql_select_players(names: List):
    names = [await to_jagex_name(n)for n in names]
    sql = "SELECT * FROM Players WHERE normalized_name in :names"
    param = {"names": names}
    data = await execute_sql(sql, param)
    
    return [] if not data else data.rows2dict()


async def parse_detection(data:dict) -> dict:
    gmt = time.gmtime(data['ts'])
    human_time = time.strftime('%Y-%m-%d %H:%M:%S', gmt)

    equipment = data.get('equipment')

    param = {
        'reportedID': data.get('id'),
        'reportingID': data.get('reporter_id'),
        'region_id': data.get('region_id'),
        'x_coord': data.get('x'),
        'y_coord': data.get('y'),
        'z_coord': data.get('z'),
        'timestamp': human_time,
        'manual_detect': data.get('manual_detect'),
        'on_members_world': data.get('on_members_world'),
        'on_pvp_world': data.get('on_pvp_world'),
        'world_number': data.get('world_number'),
        'equip_head_id': equipment.get('equip_head_id'),
        'equip_amulet_id': equipment.get('equip_amulet_id'),
        'equip_torso_id': equipment.get('equip_torso_id'),
        'equip_legs_id': equipment.get('equip_legs_id'),
        'equip_boots_id': equipment.get('equip_boots_id'),
        'equip_cape_id': equipment.get('equip_cape_id'),
        'equip_hands_id': equipment.get('equip_hands_id'),
        'equip_weapon_id': equipment.get('equip_weapon_id'),
        'equip_shield_id': equipment.get('equip_shield_id'),
        'equip_ge_value': data.get('equipment_ge')
    }
    return param

async def detect(detections:List[detection], manual_detect:int) -> None:
    manual_detect = 0 if int(manual_detect) == 0 else 1

    # remove duplicates
    df = pd.DataFrame([d.dict() for d in detections])
    df.drop_duplicates(subset=['reporter', 'reported', 'region_id'], inplace=True)

    # data validation, there can only be one reporter, and it is unrealistic to send more then 5k reports.
    if len(df) > 5000 or df["reporter"].nunique() > 1:
        logger.debug('to many reports')
        return {'NOK': 'NOK'}, 400

    logger.debug(f"Received: {len(df)} from: {df['reporter'].unique()}")

    # 1) Get a list of unqiue reported names and reporter name 
    names = list(df['reported'].unique())
    names.extend(df['reporter'].unique())

    # 1.1) Normalize and validate all names
    clean_names = [await to_jagex_name(name) for name in names if await is_valid_rsn(name)]

    # 2) Get IDs for all unique names
    data = await sql_select_players(clean_names)

    # 3) Create entries for players that do not yet exist in Players table
    existing_names = [d["normalized_name"] for d in data]
    new_names = set([name for name in clean_names]).difference(existing_names)
    
    # 3.1) Get those players' IDs from step 3
    if new_names:
        sql = "insert ignore into Players (name, normalized_name) values (:name, :nname)"
        param = [{"name": name, "nname":name} for name in new_names]

        await execute_sql(sql, param)

        data.extend(await sql_select_players(new_names))

    # 4) Insert detections into Reports table with user ids 
    # 4.1) add reported & reporter id
    df_names = pd.DataFrame(data)
    df = df.merge(df_names, left_on="reported", right_on="name")

    df["reporter_id"]  = df_names.query(f"name == {df['reporter'].unique()}")['id'].to_list()[0]
    df['manual_detect'] = manual_detect
    # 4.2) parse data to param
    data = df.to_dict('records')
    param = [await parse_detection(d) for d in data]

    # 4.3) parse query
    params = list(param[0].keys())
    columns = list_to_string(params)
    values = list_to_string([f':{column}' for column in params])

    sql = f'insert ignore into Reports ({columns}) values ({values})'
    await execute_sql(sql, param)

async def offload_detect(detections:List[detection], manual_detect:int) -> None:
    await run_in_process(detect, detections, manual_detect)

@router.post('/{version}/plugin/detect/{manual_detect}', tags=['legacy'])
async def post_detect(
        detections:List[detection],
        version:str=None, 
        manual_detect:int=0
    ):
    asyncio.create_task(
        detect(detections, manual_detect)
    )
    return {'ok':'ok'}

'''CONTRIBUTIONS ROUTE'''
class contributor(BaseModel):
    name: str

async def sql_get_contributions(contributors: List):
    query = ("""
        SELECT
            ifnull(rs.manual_detect,0) as detect,
            rs.reportedID as reported_ids,
            ban.confirmed_ban as confirmed_ban,
            ban.possible_ban as possible_ban,
            ban.confirmed_player as confirmed_player
        FROM Reports as rs
        JOIN Players as pl on (pl.id = rs.reportingID)
        join Players as ban on (ban.id = rs.reportedID)
        WHERE 1=1
            AND pl.name in :contributors
    """)

    param = {
        "contributors": contributors
    }

    output = []

    page = 1
    while True:
        data = await execute_sql(query, param=param, page=page)
        data_dict = data.rows2dict()
        output.extend(data_dict)
        if len(data_dict) < 100_000:
            break
        page += 1

    return output

async def sql_get_feedback_submissions(voters: List):
    sql = '''
        SELECT 
            PredictionsFeedback.id
        FROM PredictionsFeedback 
        JOIN Players ON Players.id = PredictionsFeedback.voter_id
        WHERE 1=1
            AND Players.name IN :voters
     '''

    params = {
        "voters": voters
    }

    data = await execute_sql(sql, param=params, debug=False, row_count=100_000_000)
    return data.rows2dict()

async def parse_contributors(contributors, version=None, add_patron_stats:bool=False):
    contributions = await sql_get_contributions(contributors)

    df = pd.DataFrame(contributions)

    df.drop_duplicates(inplace=True, subset=["reported_ids", "detect"], keep="last")

    df_detect_manual = df.loc[df['detect'] == 1]
    manual_dict = {
        "reports": len(df_detect_manual.index),
        "bans": int(df_detect_manual['confirmed_ban'].sum()),
        "possible_bans": int(df_detect_manual['possible_ban'].sum()),
        "incorrect_reports": int(df_detect_manual['confirmed_player'].sum())
    }
    manual_dict["possible_bans"] = manual_dict["possible_bans"] - manual_dict["bans"]

    df_detect_passive = df.loc[df['detect'] == 0]

    passive_dict = {
        "reports": len(df_detect_passive.index),
        "bans": int(df_detect_passive['confirmed_ban'].sum()),
        "possible_bans": int(df_detect_passive['possible_ban'].sum())
    }
    passive_dict["possible_bans"] = passive_dict["possible_bans"] - passive_dict["bans"]


    total_dict = {
        "reports": passive_dict['reports'] + manual_dict['reports'],
        "bans": passive_dict['bans'] + manual_dict['bans'],
        "possible_bans": passive_dict['possible_bans'] + manual_dict['possible_bans'],
        'feedback': len(await sql_get_feedback_submissions(contributors))
    }

    if version in ['1.3','1.3.1'] or None:
        return total_dict

    return_dict = {
        "passive": passive_dict,
        "manual": manual_dict,
        "total": total_dict
    }

    if not add_patron_stats:
        return return_dict
    
    total_dict["total_xp_removed"] = 0
    
    if df.empty:
        return_dict['total'] = total_dict
        return return_dict
 
    banned_df = df[df["confirmed_ban"] == 1]
    banned_ids = banned_df["reported_ids"].tolist()

    total_xp_sql = '''
        SELECT
            SUM(total) as total_xp
        FROM playerHiscoreDataLatest
        WHERE Player_id IN :banned_ids
    '''

    total_xp_data = await execute_sql(sql=total_xp_sql, param={"banned_ids": banned_ids})
    
    if not total_xp_data:
        return_dict['total'] = total_dict
        return return_dict

    total_xp = total_xp_data.rows2dict()[0].get("total_xp", 0)
    total_dict["total_xp_removed"] = total_xp
    return_dict['total'] = total_dict
    return return_dict

@router.post('/stats/contributions/', tags=['legacy'])
async def get_contributions(contributors: List[contributor], token:str=None):
    add_patron_stats = False
    if token:
        await verify_token(token, verifcation='verify_players')
        add_patron_stats = True
        
    contributors = [d.__dict__['name'] for d in contributors]
    
    data = await parse_contributors(contributors, version=None, add_patron_stats=add_patron_stats)
    return data

@router.get('/{version}/stats/contributions/{contributor}', tags=['legacy'])
async def get_contributions_url(contributor: str, version: str):
    data = await parse_contributors([contributor], version=version)
    return data