from typing import Optional

from fastapi.exceptions import HTTPException

from database.functions import execute_sql, list_to_string, verify_token
from fastapi import APIRouter, status
from pydantic import BaseModel


router = APIRouter()


#!sweg/!equip
# /last_sighting/?token={token}&player_name={player_name}
@router.post("/v1/last_sighting/", status_code=status.HTTP_200_OK, tags=["discord"])
async def get_last_equipment(token: str, player_name: str):
    
    if not await verify_token(token=token, verifcation="hiscore"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Insufficient rights")

    sql = '''
            SELECT *
            FROM Reports rpts
            JOIN Players pls on pls.id = rpts.reportedID
            WHERE 1 = 1
                AND pls.name = :player_name
            ORDER BY rpts.timestamp DESC
        '''

    cursor = await execute_sql(sql=sql, param={"player_name": player_name}, debug=False, row_count=1)

    return cursor.rows2dict()
    

#!gainz/!xpgains
@router.post("/v1/xp_gains/", status_code=status.HTTP_200_OK, tags=["discord"])
async def get_xp_gains(token: str, player_name: str):

    if not await verify_token(token=token, verifcation="hiscore"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Insufficient rights")

    sql = '''          
            SELECT * 
            FROM playerHiscoreDataXPChange xp
            JOIN Players pls on pls.id = xp.Player_id
            WHERE 1 = 1
                AND pls.name = :player_name
            ORDER BY xp.timestamp DESC
        '''

    cursor = await execute_sql(sql=sql, param={"player_name": player_name}, debug=False, row_count=2)

    return cursor.rows2dict()

