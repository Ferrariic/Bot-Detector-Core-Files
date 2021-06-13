import os, sys

from sqlalchemy.sql.expression import column
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import pandas as pd
import numpy as np
from joblib import dump, load
import concurrent.futures as cf

from sklearn.ensemble import VotingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.calibration import CalibratedClassifierCV

# custom imports
import SQL, Config, SQL_folder
from scraper import hiscoreScraper as highscores
from Predictions import prediction_functions as pf
from Predictions import extra_data as ed
import traceback

def create_model():
    rfc = RandomForestClassifier(n_estimators=100, random_state=7, n_jobs=-1)
    return rfc


def process(df, scaler=None, transformer=None):
    # cleaning
    try:
        df_clean = (df
            .pipe(pf.start_pipeline)
            .pipe(pf.clean_dataset, ed.skills_list, ed.minigames_list)
            .pipe(pf.f_features,    ed.skills_list, ed.minigames_list)
            .pipe(pf.filter_relevant_features, ed.skills_list)
        )
    except Exception as e:
        Config.debug(f'Error cleaning: {e}')
        return None, None

    # preprocess
    try:
        df_preprocess = (df_clean
            .pipe(pf.start_pipeline)
            .pipe(pf.f_standardize, scaler)
            .pipe(pf.f_normalize, transformer)
        )
    except Exception as e:
        Config.debug(f'Error normalizing: {e}')
        return None, None

    return df_clean, df_preprocess


def train_model(n_pca='mle', use_pca=True):
    Config.debug(f'Train Model config: n_pca: {n_pca}, use_pca: {use_pca}')
    # get data
    df =            pf.get_highscores()
    df_players =    pf.get_players()
    df_labels =     pf.get_labels() 


    df_clean, df_preprocess = process(df)

    today = int(time.time()) # time.strftime('%Y-%m-%d', time.gmtime())

    columns = df_preprocess.columns.tolist()
    dump(value=columns, filename=f'Predictions/models/features_{today}_100.joblib')
    

    df_pca, pca_model = pf.f_pca(df_preprocess, n_components=n_pca, pca=None)
    # dump(value=pca_model, filename=f'Predictions/models/pca_{today}_{n_pca}.joblib')

    if not use_pca:
        df_pca = df_preprocess
    
    Config.debug(f'pca shape: {df_pca.shape}')

    df_pca = df_pca.merge(df_players,   left_index=True,    right_index=True, how='inner')
    df_pca = df_pca.merge(df_labels,    left_on='label_id', right_index=True, how='left')

    lbls = [
        'Real_Player', 'Smithing_bot', 'Mining_bot', 
        'Magic_bot', 'PVM_Ranged_bot', 
        'Fletching_bot', 'PVM_Melee_bot', 'Herblore_bot',
        'Thieving_bot','Crafting_bot', 'PVM_Ranged_Magic_bot',
        'Hunter_bot','Runecrafting_bot','Fishing_bot','Agility_bot',
        'Cooking_bot', 'mort_myre_fungus_bot',
        'Woodcutting_bot', 'Firemaking_bot','Fishing_Cooking_bot'
    ]

    Config.debug(f'labels: {len(lbls)}, {lbls}')

    # creating x, y data, with players that a label
    mask = ~(df_pca['label_id'] == 0) & (df_pca['label'].isin(lbls))
    df_labeled = df_pca[mask].copy()
    df_labeled.drop(columns=['confirmed_ban','confirmed_player','possible_ban','label_id'], inplace=True)
    x, y = df_labeled.iloc[:,:-1], df_labeled.iloc[:,-1]

    Config.debug(f'x shape:{x.shape}')
    Config.debug(f'y shape:{y.shape}')

    # save labels
    lbls = np.sort(y.unique())
    dump(value=lbls, filename=f'Predictions/models/labels_{today}_100.joblib')

    # train test split but make sure to have all the labels form y
    train_x, test_x, train_y, test_y = train_test_split(x, y, test_size=0.3, random_state=42, stratify=y)

    model_name = 'rfc'
    model = create_model()
    model = model.fit(train_x, train_y)

    # print model score
    model_score = round(model.score(test_x, test_y)*100,2)
    Config.debug(f'Score: {model_score}')

    # print more detailed model score
    Config.debug(classification_report(test_y, model.predict(test_x), target_names=lbls))

    # fit & save model on entire dataset
    model = model.fit(x, y)
    dump(value=model, filename=f'Predictions/models/model-{model_name}_{today}_{model_score}.joblib')

    return


def load_models():
    try:
        scaler, _ = pf.best_file_path(startwith='scaler', dir='Predictions/models')
        scaler = load(scaler)

        transformer, _ = pf.best_file_path(startwith='normalizer', dir='Predictions/models')
        transformer = load(transformer)

        features, _ = pf.best_file_path(startwith='features', dir='Predictions/models')
        features = load(features)

        pca, n_pca = pf.best_file_path(startwith='pca', dir='Predictions/models')
        pca = load(pca)

        labels, _ = pf.best_file_path(startwith='labels', dir='Predictions/models')
        labels = load(labels)

        model, _ = pf.best_file_path(startwith='model', dir='Predictions/models')
        model = load(model)
        
        return [scaler, transformer, features, pca, n_pca, labels, model]
    except Exception as e:
        Config.debug(f'Error loading: {e}')
        return None


def get_batched_players(start, amount):
    Config.debug(f'get_hiscores: {start}, {amount}')

    df = pf.get_highscores(ofinterest=False, start=start, amount=amount)
    ids = df['Player_id'].to_list()

    df_players = pf.get_players(with_id=True, ofinterest=False, ids=ids)
    return df, df_players


def get_prediction_from_db(player):
    try:
        df_resf = SQL.get_prediction_player(player.id)
        df_resf = pd.DataFrame(df_resf)
        df_resf.set_index('name', inplace=True)
        df_resf.rename(columns={'Predicted_confidence': 'Predicted confidence'}, inplace=True)

        t = pd.Timestamp('now') + pd.Timedelta(-24, unit='H')

        if pd.to_datetime(df_resf['created'].values[0]) < t:
            Config.debug(f'old prediction: {df_resf["created"].values}')
            return None

        columns = [c for c in df_resf.columns.tolist() if not(c in ['id','prediction', 'created'])]
        df_resf.loc[:, columns]= df_resf[columns].astype(float)/100
        Config.debug('from db')

        return df_resf
    except Exception as e:
        Config.debug(f'error in get_prediction_from_db: {e}')
        Config.debug(traceback.print_exc())
        # prediction is not in the database
        return None


def predict_model(player_name=None, start=0, amount=100_000, use_pca=True, debug=False):
    old_prediction = False
    # load scaler, transformer, features, pca, labels & model
    models = load_models()

    if models is None:
        prediction_data = {
            "player_id": -1,
            "player_name": player_name,
            "prediction_label": "Error: The machine is learning",
            "prediction_confidence": 0,
            "secondary_predictions": []
        }
        return prediction_data

    scaler, transformer, features, pca, n_pca, labels, model = models

    # if no player name is given, take all players
    # if a player name is given, check if we have a record for this player else scrape that player
    if player_name is None:
        df, df_players = get_batched_players(start, amount)
    else:
        player = SQL.get_player(player_name)

        if player is None or debug:
            _ = highscores.scrape_one(player_name)
            player = SQL.get_player(player_name)
            df =  SQL.get_highscores_data(0, 1, player.name)
            old_prediction = True
            Config.debug('hiscores')
        else:
            df_resf = get_prediction_from_db(player)
            if df_resf is not None:
                return df_resf

            # player has no stored or old prediction
            old_prediction = True
            # df = highscores.scrape_one(player_name)########################
            df =  SQL.get_highscores_data(0, 1, player.name)
            Config.debug('hiscores')
            # player is not on the hiscores
            if df == (None, None):
                prediction_data = {
                    "player_id": -1,
                    "player_name": player_name,
                    "prediction_label": "Player not on highscores",
                    "prediction_confidence": 0,
                    "secondary_predictions": []
                }
                return prediction_data
            
        df = pd.DataFrame(df)
        df_players = pf.get_players(players=pd.DataFrame([player]), with_id=True)
        

    df_clean, df_preprocess = process(df, scaler, transformer)

    if df_clean is None:
        Config.debug(f' {player_name}')
        Config.debug(f' {df}')
        prediction_data = {
            "player_id": -1,
            "player_name": player_name,
            "prediction_label": "Not In Our Database",
            "prediction_confidence": 0,
            "secondary_predictions": []
        }
        return prediction_data

    df_preprocess = df_preprocess[features].copy()

    Config.debug(f'Predict Model config: n_pca: {n_pca}, use_pca: {use_pca}')
    
    if use_pca:
        df_pca, pca_model = pf.f_pca(df_preprocess, n_components=n_pca, pca=pca)
    else:
        df_pca = df_preprocess

    Config.debug(f'pca shape: {df_pca.shape}')
    
    proba =         model.predict_proba(df_pca)
    df_proba_max =  proba.max(axis=1)
    pred =          model.predict(df_pca)

    df_gnb_proba_max =      pd.DataFrame(df_proba_max,  index=df_pca.index, columns=['Predicted confidence'])
    df_gnb_predictions =    pd.DataFrame(pred,          index=df_pca.index, columns=['prediction'])
    df_gnb_proba =          pd.DataFrame(proba,         index=df_pca.index, columns=labels).round(4)

    df_resf = df_players[['id']].copy()
    df_resf['created'] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    df_resf = df_resf.merge(df_gnb_predictions, left_index=True, right_index=True, suffixes=('', '_prediction'),how='inner')
    df_resf = df_resf.merge(df_gnb_proba_max,   left_index=True, right_index=True, how='inner')
    df_resf = df_resf.merge(df_gnb_proba,       left_index=True, right_index=True, suffixes=('', '_probability'), how='inner')

    if old_prediction:
        Config.debug(f'old prediction, inserting {player.name}, prediction: {df_resf["prediction"].to_list()}, confidence:{df_resf["Predicted confidence"].to_list()}')
        insert_into_db(df_resf.copy())

    return df_resf


def prepare_data_for_db(df):
    # parse predictions to int
    int_columns = [c for c in df.columns.tolist() if c not in ['id','prediction', 'created']]
    df[int_columns] = df[int_columns].astype(float)*100
    df[int_columns] = df[int_columns].round(2)
    df['id'] = df['id'].astype(int)

    # replace spaces in column names to _
    df.columns = [c.replace(' ','_') for c in df.columns.tolist()]

    # remove predictioin because this is text
    columns = df.columns.tolist()
    columns.remove('prediction')
    columns.remove('id')
    columns.remove('created')
    return df, columns

def insert_prepared_data(df, columns):
    # add prediction back as first field
    ordered_columns = ['prediction','id', 'created'] + columns
    df = df[ordered_columns]
    df.reset_index(inplace=True) # first column will be name
    
    # row to dict
    data = df.to_dict('records')
    length = len(df)

    # insert many
    row = data[0]
    values = SQL.list_to_string([f':{column}' for column in list(row.keys())])
    sql_insert = f'replace into Predictions values ({values});'
    SQL.execute_sql(sql_insert, param=data, debug=False, has_return=False)
    return length

def insert_into_db(df):
    df, columns = prepare_data_for_db(df)
    length = insert_prepared_data(df, columns)
    return
    
def save_model(n_pca='mle', use_pca=True):
    Config.debug(os.listdir())
    Config.debug(f'Save Model config: n_pca {n_pca}, use_pca {use_pca}')
    # chunking data
    limit = 5_000
    end = False
    first_run = True
    loop = 0

    train_model(n_pca, use_pca)

    # get predictions in chunks
    while not(end):
        start = loop * limit
        df = predict_model(player_name=None, start=start, amount=limit, use_pca=use_pca)
        Config.debug(f'data shape: {df.shape}')

        df, columns = prepare_data_for_db(df)

        # if the first run then drop & create table
        if first_run:
            Config.debug('drop & create table')
            first_run = False

            table_name = 'Predictions'
            droptable = f'DROP TABLE IF EXISTS {table_name};'
            createtable = f'CREATE TABLE IF NOT EXISTS {table_name} (name varchar(12), prediction varchar(50), id INT, created TIMESTAMP, {" DECIMAL(5,2), ".join(columns)} DECIMAL(5,2));'
            indexname = 'ALTER TABLE playerdata.Predictions ADD UNIQUE name (name);'
            fk = 'ALTER TABLE `Predictions` ADD CONSTRAINT `FK_pred_player_id` FOREIGN KEY (`id`) REFERENCES `Players`(`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;'

            SQL.execute_sql(droptable,      param=None, debug=False, has_return=False)
            SQL.execute_sql(createtable,    param=None, debug=False, has_return=False)
            SQL.execute_sql(indexname,      param=None, debug=False, has_return=False)
            SQL.execute_sql(fk,             param=None, debug=False, has_return=False)

        length = insert_prepared_data(df, columns)

        loop += 1

        if length < limit:
            end = True
    return



if __name__ == '__main__':
    use_pca = False
    debug = False
    n_pca = 2
    
    players = [
        'NagatoRyoma',
        'Alex3976',
        'Hosuke79999',
        'AsukaYuri',
        'EchizenLee',
        'Feastyakorb',
        '5 Fort Open',
        'PegasusFuma',
        'Cross55612',
        'Hyuga42096',
        'Kira58769',
        'AsheIvern',
        'MitsukiRock'
    ]
    
    train_model(use_pca=use_pca, n_pca=n_pca)
    # save_model(use_pca=use_pca, n_pca=n_pca)

    for player in players:
        df = predict_model(player_name=player, use_pca=use_pca, debug=debug) # player_name='extreme4all'
        print(df.head())
