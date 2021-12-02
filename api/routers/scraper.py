import asyncio
import logging
import random
import time
from typing import List, Optional

from api.database.database import Engine
from api.database.functions import (batch_function, execute_sql, verify_token)
from api.database.models import Player as dbPlayer
from api.database.models import playerHiscoreData
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.exc import InternalError
from sqlalchemy.sql.expression import insert, update

logger = logging.getLogger(__name__)
router = APIRouter()

class hiscore(BaseModel):
    Player_id: int
    total: int
    Attack: int
    Defence: int
    Strength: int
    Hitpoints: int
    Ranged: int
    Prayer: int
    Magic: int
    Cooking: int
    Woodcutting: int
    Fletching: int
    Fishing: int
    Firemaking: int
    Crafting: int
    Smithing: int
    Mining: int
    Herblore: int
    Agility: int
    Thieving: int
    Slayer: int
    Farming: int
    Runecraft: int
    Hunter: int
    Construction: int
    league: int
    bounty_hunter_hunter: int
    bounty_hunter_rogue: int
    cs_all: int
    cs_beginner: int
    cs_easy: int
    cs_medium: int
    cs_hard: int
    cs_elite: int
    cs_master: int
    lms_rank: int
    soul_wars_zeal: int
    abyssal_sire: int
    alchemical_hydra: int
    barrows_chests: int
    bryophyta: int
    callisto: int
    cerberus: int
    chambers_of_xeric: int
    chambers_of_xeric_challenge_mode: int
    chaos_elemental: int
    chaos_fanatic: int
    commander_zilyana: int
    corporeal_beast: int
    crazy_archaeologist: int
    dagannoth_prime: int
    dagannoth_rex: int
    dagannoth_supreme: int
    deranged_archaeologist: int
    general_graardor: int
    giant_mole: int
    grotesque_guardians: int
    hespori: int
    kalphite_queen: int
    king_black_dragon: int
    kraken: int
    kreearra: int
    kril_tsutsaroth: int
    mimic: int
    nightmare: int
    obor: int
    sarachnis: int
    scorpia: int
    skotizo: int
    tempoross:int
    the_gauntlet: int
    the_corrupted_gauntlet: int
    theatre_of_blood: int
    theatre_of_blood_hard: int
    thermonuclear_smoke_devil: int
    tzkal_zuk: int
    tztok_jad: int
    venenatis: int
    vetion: int
    vorkath: int
    wintertodt: int
    zalcano: int
    zulrah: int

class Player(BaseModel):
    id: int
    name: Optional[str]
    possible_ban: Optional[bool]
    confirmed_ban: Optional[bool]
    confirmed_player: Optional[bool]
    label_id: Optional[int]
    label_jagex: Optional[int]

class scraper(BaseModel):
    hiscores: Optional[hiscore]
    player: Player

async def sql_get_players_to_scrape(page=1, amount=100_000):
    sql = 'select * from playersToScrape WHERE 1 ORDER BY RAND()'
    data = await execute_sql(sql, page=page, row_count=amount)
    return data.rows2dict()

@router.get("/scraper/players/{page}/{amount}/{token}", tags=["scraper"])
async def get_players_to_scrape(token, page:int=1, amount:int=100_000):
    await verify_token(token, verifcation='ban')
    return await sql_get_players_to_scrape(page=page, amount=amount)

async def sqla_update_player(players):
    Session = Engine().session
    async with Session() as session:
        for player in players:
            player_id = player.pop('id')
            sql = update(dbPlayer).where(id==player_id)
            await session.execute(sql, player)
        await session.commit()
    return

async def sqla_insert_hiscore(hiscores):
    sql = insert(playerHiscoreData).prefix_with('ignore')

    Session = Engine().session
    try:
        async with Session() as session:
            await session.execute(sql, hiscores)
            await session.commit()
    except InternalError:
        logger.debug('Lock wait timeout exceeded')
        await asyncio.sleep(random.uniform(1,5.1))
        await sqla_insert_hiscore(hiscores)
    return

@router.post("/scraper/hiscores/{token}", tags=["scraper"])
async def post_hiscores_to_db(token, data: List[scraper]):
    await verify_token(token, verifcation='ban')

    # get all players & all hiscores
    data = [d.dict() for d in data]
    players = []
    hiscores = []
    for d in data:
        player_dict = d['player']
        hiscore_dict = d['hiscores']

        # add extra data
        time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        player_dict['updated_at'] = time_now
        
        players.append(player_dict)

        if hiscore_dict:
            hiscores.append(hiscore_dict)
    # batchwise insert & update
    await batch_function(sqla_insert_hiscore, hiscores, batch_size=500)
    await batch_function(sqla_update_player, players, batch_size=500)
    return {'ok':'ok'}
    
