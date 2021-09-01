from Config import app
from routers import discord, feedback, hiscore, legacy, player, prediction, report

app.include_router(hiscore.router)
app.include_router(discord.router)
app.include_router(player.router)
app.include_router(prediction.router)
app.include_router(feedback.router)
app.include_router(report.router)
app.include_router(legacy.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
