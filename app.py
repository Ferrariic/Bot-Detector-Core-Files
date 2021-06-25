from time import sleep
from flask import config, jsonify, redirect, make_response
from waitress import serve
import datetime as dt
import os
# custom
import Config
from scraper import hiscoreScraper, banned_by_jagex
from mysite.tokens import app_token
from mysite.dashboard import dashboard
from plugin.plugin_stats import plugin_stats
from plugin.detect import detect
from Config import app, sched
from mysite.predictions import app_predictions
from Predictions import model
from discord.discord import discord
from scraper.scraper import app_scraper
from plugin.clan import clan
from player.player import player
import gc

app.register_blueprint(plugin_stats)
app.register_blueprint(detect)
app.register_blueprint(app_token)
app.register_blueprint(dashboard)
app.register_blueprint(app_predictions)
app.register_blueprint(discord)
app.register_blueprint(app_scraper)
app.register_blueprint(clan)
app.register_blueprint(player)

def print_jobs():
    Config.debug('   Scheduled Jobs:')
    for job in sched.get_jobs():
        Config.debug(f'    Job: {job.name}, {job.trigger}, {job.func}')
    return
def gb_collector():
    Config.debug(f"Garbage Collector stats: {gc.get_stats()}")
    return

if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    started = True
    Config.debug(f'devmode: {Config.dev_mode}')

    # prevent scraping & predicting for every player in dev
    if not(int(Config.dev_mode)):
        Config.debug('Live version')
        day = dt.datetime.combine(dt.date.today(), dt.datetime.min.time())
        save_model_time = day + dt.timedelta(hours=15)

        # sched.add_job(model.save_model, args=[n_pca], trigger='interval', days=1, start_date=today18h, replace_existing=True, name='save_model')
        sched.add_job(banned_by_jagex.confirm_possible_ban, trigger='interval', days=1, start_date=dt.date.today(), replace_existing=True, name='confirm_possible_ban')

        sched.add_job(hiscoreScraper.run_scraper, trigger='interval', minutes=1,start_date=dt.date.today(), name='run_hiscore', max_instances=10, coalesce=True)
        
    sched.add_job(model.train_model, args=[Config.n_pca, Config.use_pca], replace_existing=True, name='train_model')  # on startup
    sched.add_job(gb_collector, trigger='interval',hours=1, start_date=dt.date.today())

    print_jobs()
    sched.start()
# do we need this?
else:
    started = False


@app.errorhandler(404)
def page_not_found(e):
    Config.debug(e)
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

  
@app.route("/")
def hello():
    data = {'welcome': 'test', 'job': started}
    return jsonify(data)

  
@app.route("/favicon.ico")
def favicon():
    return "", 200
    

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="ratelimit exceeded %s" % e.description), 429

if __name__ == '__main__':
    # app.run(port=flask_port, debug=True, use_reloader=False)
    serve(app, host='127.0.0.1', port=Config.flask_port)
    #meaningless comment