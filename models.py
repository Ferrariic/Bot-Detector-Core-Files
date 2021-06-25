# coding: utf-8
from sqlalchemy import (DECIMAL, TIMESTAMP, BigInteger, Column, Date, DateTime,
                        Float, ForeignKey, Index, Integer, String, Table, Text,
                        text)
from sqlalchemy.dialects.mysql import TEXT, TINYINT, TINYTEXT, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
metadata = Base.metadata


class LabelJagex(Base):
    __tablename__ = 'LabelJagex'

    id = Column(Integer, primary_key=True)
    label = Column(String(50), nullable=False)


class Label(Base):
    __tablename__ = 'Labels'

    id = Column(Integer, primary_key=True, unique=True)
    label = Column(VARCHAR(50), nullable=False)


class PlayerBotConfirmation(Base):
    __tablename__ = 'PlayerBotConfirmation'
    __table_args__ = (
        Index('Unique_player_label_bot', 'player_id',
              'label_id', 'bot', unique=True),
    )

    id = Column(Integer, primary_key=True)
    ts = Column(TIMESTAMP, nullable=False,
                server_default=text("CURRENT_TIMESTAMP"))
    player_id = Column(Integer, nullable=False)
    label_id = Column(Integer, nullable=False)
    bot = Column(TINYINT(1), nullable=False)


class PlayersChange(Base):
    __tablename__ = 'PlayersChanges'

    id = Column(Integer, primary_key=True)
    ChangeDate = Column(TIMESTAMP, nullable=False,
                        server_default=text("CURRENT_TIMESTAMP"))
    player_id = Column(Integer, nullable=False)
    name = Column(String(15), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    possible_ban = Column(TINYINT(1), nullable=False,
                          server_default=text("'0'"))
    confirmed_ban = Column(TINYINT(1), nullable=False,
                           server_default=text("'0'"))
    confirmed_player = Column(
        TINYINT(1), nullable=False, server_default=text("'0'"))
    label_id = Column(Integer, nullable=False, index=True,
                      server_default=text("'0'"))
    label_jagex = Column(Integer, nullable=False, server_default=text("'0'"))


class Token(Base):
    __tablename__ = 'Tokens'

    id = Column(Integer, primary_key=True)
    player_name = Column(VARCHAR(50), nullable=False)
    token = Column(String(50), nullable=False)
    request_highscores = Column(
        TINYINT(1), nullable=False, server_default=text("'0'"))
    verify_ban = Column(TINYINT(1), nullable=False, server_default=text("'0'"))
    create_token = Column(TINYINT(1), nullable=False,
                          server_default=text("'0'"))
    verify_players = Column(TINYINT(1), nullable=False,
                            server_default=text("'0'"))
    discord_general = Column(TINYINT(1), nullable=False,
                             server_default=text("'0'"))


class PlayerHiscoreDataChange(Base):
    __tablename__ = 'playerHiscoreDataChanges'

    id = Column(Integer, primary_key=True)
    playerHiscoreDataID = Column(Integer, nullable=False)
    old_player_id = Column(Integer, nullable=False)
    new_player_id = Column(Integer, nullable=False)
    old_total = Column(Integer, nullable=False)
    new_total = Column(Integer, nullable=False)
    change_at = Column(TIMESTAMP, nullable=False,
                       server_default=text("CURRENT_TIMESTAMP"))


class RegionIDName(Base):
    __tablename__ = 'regionIDNames'

    entry_ID = Column(Integer, primary_key=True)
    region_ID = Column(Integer, nullable=False, unique=True)
    z_axis = Column(Integer, server_default=text("'0'"))
    region_name = Column(Text, nullable=False)


class ReportLatest(Base):
    __tablename__ = 'reportLatest'

    report_id = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    reported_id = Column(Integer, primary_key=True)
    region_id = Column(Integer, nullable=False)
    x_coord = Column(Integer, nullable=False)
    y_coord = Column(Integer, nullable=False)
    z_coord = Column(Integer, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    on_members_world = Column(Integer)
    world_number = Column(Integer)
    equip_head_id = Column(Integer)
    equip_amulet_id = Column(Integer)
    equip_torso_id = Column(Integer)
    equip_legs_id = Column(Integer)
    equip_boots_id = Column(Integer)
    equip_cape_id = Column(Integer)
    equip_hands_id = Column(Integer)
    equip_weapon_id = Column(Integer)
    equip_shield_id = Column(Integer)
    equip_ge_value = Column(BigInteger)


class SentToJagex(Base):
    __tablename__ = 'sentToJagex'

    entry_id = Column(Integer, primary_key=True)
    created_on = Column(TIMESTAMP, nullable=False,
                        server_default=text("CURRENT_TIMESTAMP"))
    name = Column(Text, nullable=False)


class LabelSubGroup(Base):
    __tablename__ = 'LabelSubGroup'

    id = Column(Integer, primary_key=True)
    parent_label = Column(ForeignKey(
        'Labels.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False, index=True)
    child_label = Column(ForeignKey('Labels.id', ondelete='RESTRICT',
                         onupdate='RESTRICT'), nullable=False, index=True)

    Label = relationship(
        'Label', primaryjoin='LabelSubGroup.child_label == Label.id')
    Label1 = relationship(
        'Label', primaryjoin='LabelSubGroup.parent_label == Label.id')


class Player(Base):
    __tablename__ = 'Players'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False,
                        server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime)
    possible_ban = Column(TINYINT(1), nullable=False,
                          server_default=text("'0'"))
    confirmed_ban = Column(TINYINT(1), nullable=False,
                           index=True, server_default=text("'0'"))
    confirmed_player = Column(
        TINYINT(1), nullable=False, server_default=text("'0'"))
    label_id = Column(ForeignKey('Labels.id', ondelete='RESTRICT', onupdate='RESTRICT'),
                      nullable=False, index=True, server_default=text("'0'"))
    label_jagex = Column(Integer, nullable=False, server_default=text("'0'"))

    label = relationship('Label')


class PredictionsFeedback(Base):
    __tablename__ = 'PredictionsFeedback'
    __table_args__ = (
        Index('UNIQUE_VOTE', 'voter_id', 'prediction',
              'subject_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    ts = Column(TIMESTAMP, nullable=False,
                server_default=text("CURRENT_TIMESTAMP"))
    voter_id = Column(ForeignKey(
        'Players.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)
    subject_id = Column(ForeignKey('Players.id', ondelete='RESTRICT',
                        onupdate='RESTRICT'), nullable=False, index=True)
    prediction = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    vote = Column(Integer, nullable=False, server_default=text("'0'"))
    feedback_text = Column(TEXT)

    subject = relationship(
        'Player', primaryjoin='PredictionsFeedback.subject_id == Player.id')
    voter = relationship(
        'Player', primaryjoin='PredictionsFeedback.voter_id == Player.id')


class Report(Base):
    __tablename__ = 'Reports'
    __table_args__ = (
        Index('Unique_Report', 'reportedID', 'reportingID',
              'region_id', 'manual_detect', unique=True),
        Index('reportedID', 'reportedID', 'region_id')
    )

    ID = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP, nullable=False,
                        server_default=text("CURRENT_TIMESTAMP"))
    reportedID = Column(ForeignKey('Players.id', ondelete='RESTRICT',
                        onupdate='RESTRICT'), nullable=False, index=True)
    reportingID = Column(ForeignKey('Players.id', ondelete='RESTRICT',
                         onupdate='RESTRICT'), nullable=False, index=True)
    region_id = Column(Integer, nullable=False)
    x_coord = Column(Integer, nullable=False)
    y_coord = Column(Integer, nullable=False)
    z_coord = Column(Integer, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False,
                       server_default=text("CURRENT_TIMESTAMP"))
    manual_detect = Column(TINYINT(1))
    on_members_world = Column(Integer)
    on_pvp_world = Column(TINYINT)
    world_number = Column(Integer)
    equip_head_id = Column(Integer)
    equip_amulet_id = Column(Integer)
    equip_torso_id = Column(Integer)
    equip_legs_id = Column(Integer)
    equip_boots_id = Column(Integer)
    equip_cape_id = Column(Integer)
    equip_hands_id = Column(Integer)
    equip_weapon_id = Column(Integer)
    equip_shield_id = Column(Integer)
    equip_ge_value = Column(BigInteger)

    Player = relationship(
        'Player', primaryjoin='Report.reportedID == Player.id')
    Player1 = relationship(
        'Player', primaryjoin='Report.reportingID == Player.id')


class PlayerChatHistory(Base):
    __tablename__ = 'playerChatHistory'

    entry_id = Column(Integer, primary_key=True)
    reportedID = Column(ForeignKey('Players.id'), nullable=False, index=True)
    chat = Column(TINYTEXT, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False,
                       server_default=text("CURRENT_TIMESTAMP"))
    reportingID = Column(ForeignKey('Players.id'), nullable=False, index=True)

    Player = relationship(
        'Player', primaryjoin='PlayerChatHistory.reportedID == Player.id')
    Player1 = relationship(
        'Player', primaryjoin='PlayerChatHistory.reportingID == Player.id')


class PlayerHiscoreDatum(Base):
    __tablename__ = 'playerHiscoreData'
    __table_args__ = (
        Index('Unique_player_date', 'Player_id', 'ts_date', unique=True),
        Index('Unique_player_time', 'timestamp', 'Player_id', unique=True)
    )

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False,
                       server_default=text("CURRENT_TIMESTAMP"))
    ts_date = Column(Date)
    Player_id = Column(ForeignKey(
        'Players.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)
    total = Column(BigInteger)
    attack = Column(Integer)
    defence = Column(Integer)
    strength = Column(Integer)
    hitpoints = Column(Integer)
    ranged = Column(Integer)
    prayer = Column(Integer)
    magic = Column(Integer)
    cooking = Column(Integer)
    woodcutting = Column(Integer)
    fletching = Column(Integer)
    fishing = Column(Integer)
    firemaking = Column(Integer)
    crafting = Column(Integer)
    smithing = Column(Integer)
    mining = Column(Integer)
    herblore = Column(Integer)
    agility = Column(Integer)
    thieving = Column(Integer)
    slayer = Column(Integer)
    farming = Column(Integer)
    runecraft = Column(Integer)
    hunter = Column(Integer)
    construction = Column(Integer)
    league = Column(Integer)
    bounty_hunter_hunter = Column(Integer)
    bounty_hunter_rogue = Column(Integer)
    cs_all = Column(Integer)
    cs_beginner = Column(Integer)
    cs_easy = Column(Integer)
    cs_medium = Column(Integer)
    cs_hard = Column(Integer)
    cs_elite = Column(Integer)
    cs_master = Column(Integer)
    lms_rank = Column(Integer)
    soul_wars_zeal = Column(Integer)
    abyssal_sire = Column(Integer)
    alchemical_hydra = Column(Integer)
    barrows_chests = Column(Integer)
    bryophyta = Column(Integer)
    callisto = Column(Integer)
    cerberus = Column(Integer)
    chambers_of_xeric = Column(Integer)
    chambers_of_xeric_challenge_mode = Column(Integer)
    chaos_elemental = Column(Integer)
    chaos_fanatic = Column(Integer)
    commander_zilyana = Column(Integer)
    corporeal_beast = Column(Integer)
    crazy_archaeologist = Column(Integer)
    dagannoth_prime = Column(Integer)
    dagannoth_rex = Column(Integer)
    dagannoth_supreme = Column(Integer)
    deranged_archaeologist = Column(Integer)
    general_graardor = Column(Integer)
    giant_mole = Column(Integer)
    grotesque_guardians = Column(Integer)
    hespori = Column(Integer)
    kalphite_queen = Column(Integer)
    king_black_dragon = Column(Integer)
    kraken = Column(Integer)
    kreearra = Column(Integer)
    kril_tsutsaroth = Column(Integer)
    mimic = Column(Integer)
    nightmare = Column(Integer)
    obor = Column(Integer)
    sarachnis = Column(Integer)
    scorpia = Column(Integer)
    skotizo = Column(Integer)
    tempoross = Column(Integer)
    the_gauntlet = Column(Integer)
    the_corrupted_gauntlet = Column(Integer)
    theatre_of_blood = Column(Integer)
    theatre_of_blood_hard = Column(Integer)
    thermonuclear_smoke_devil = Column(Integer)
    tzkal_zuk = Column(Integer)
    tztok_jad = Column(Integer)
    venenatis = Column(Integer)
    vetion = Column(Integer)
    vorkath = Column(Integer)
    wintertodt = Column(Integer)
    zalcano = Column(Integer)
    zulrah = Column(Integer)

    Player = relationship('Player')


class PlayerHiscoreDataLatest(Base):
    __tablename__ = 'playerHiscoreDataLatest'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False,
                       server_default=text("CURRENT_TIMESTAMP"))
    ts_date = Column(Date)
    Player_id = Column(ForeignKey('Players.id', ondelete='RESTRICT',
                       onupdate='RESTRICT'), nullable=False, unique=True)
    total = Column(BigInteger)
    attack = Column(Integer)
    defence = Column(Integer)
    strength = Column(Integer)
    hitpoints = Column(Integer)
    ranged = Column(Integer)
    prayer = Column(Integer)
    magic = Column(Integer)
    cooking = Column(Integer)
    woodcutting = Column(Integer)
    fletching = Column(Integer)
    fishing = Column(Integer)
    firemaking = Column(Integer)
    crafting = Column(Integer)
    smithing = Column(Integer)
    mining = Column(Integer)
    herblore = Column(Integer)
    agility = Column(Integer)
    thieving = Column(Integer)
    slayer = Column(Integer)
    farming = Column(Integer)
    runecraft = Column(Integer)
    hunter = Column(Integer)
    construction = Column(Integer)
    league = Column(Integer)
    bounty_hunter_hunter = Column(Integer)
    bounty_hunter_rogue = Column(Integer)
    cs_all = Column(Integer)
    cs_beginner = Column(Integer)
    cs_easy = Column(Integer)
    cs_medium = Column(Integer)
    cs_hard = Column(Integer)
    cs_elite = Column(Integer)
    cs_master = Column(Integer)
    lms_rank = Column(Integer)
    soul_wars_zeal = Column(Integer)
    abyssal_sire = Column(Integer)
    alchemical_hydra = Column(Integer)
    barrows_chests = Column(Integer)
    bryophyta = Column(Integer)
    callisto = Column(Integer)
    cerberus = Column(Integer)
    chambers_of_xeric = Column(Integer)
    chambers_of_xeric_challenge_mode = Column(Integer)
    chaos_elemental = Column(Integer)
    chaos_fanatic = Column(Integer)
    commander_zilyana = Column(Integer)
    corporeal_beast = Column(Integer)
    crazy_archaeologist = Column(Integer)
    dagannoth_prime = Column(Integer)
    dagannoth_rex = Column(Integer)
    dagannoth_supreme = Column(Integer)
    deranged_archaeologist = Column(Integer)
    general_graardor = Column(Integer)
    giant_mole = Column(Integer)
    grotesque_guardians = Column(Integer)
    hespori = Column(Integer)
    kalphite_queen = Column(Integer)
    king_black_dragon = Column(Integer)
    kraken = Column(Integer)
    kreearra = Column(Integer)
    kril_tsutsaroth = Column(Integer)
    mimic = Column(Integer)
    nightmare = Column(Integer)
    obor = Column(Integer)
    sarachnis = Column(Integer)
    scorpia = Column(Integer)
    skotizo = Column(Integer)
    Tempoross = Column(Integer, nullable=False)
    the_gauntlet = Column(Integer)
    the_corrupted_gauntlet = Column(Integer)
    theatre_of_blood = Column(Integer)
    theatre_of_blood_hard = Column(Integer)
    thermonuclear_smoke_devil = Column(Integer)
    tzkal_zuk = Column(Integer)
    tztok_jad = Column(Integer)
    venenatis = Column(Integer)
    vetion = Column(Integer)
    vorkath = Column(Integer)
    wintertodt = Column(Integer)
    zalcano = Column(Integer)
    zulrah = Column(Integer)

    Player = relationship('Player')


class PlayerHiscoreDataXPChange(Base):
    __tablename__ = 'playerHiscoreDataXPChange'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False,
                       server_default=text("CURRENT_TIMESTAMP"))
    ts_date = Column(Date)
    Player_id = Column(ForeignKey('Players.id', ondelete='RESTRICT',
                       onupdate='RESTRICT'), nullable=False, index=True)
    total = Column(BigInteger)
    attack = Column(Integer)
    defence = Column(Integer)
    strength = Column(Integer)
    hitpoints = Column(Integer)
    ranged = Column(Integer)
    prayer = Column(Integer)
    magic = Column(Integer)
    cooking = Column(Integer)
    woodcutting = Column(Integer)
    fletching = Column(Integer)
    fishing = Column(Integer)
    firemaking = Column(Integer)
    crafting = Column(Integer)
    smithing = Column(Integer)
    mining = Column(Integer)
    herblore = Column(Integer)
    agility = Column(Integer)
    thieving = Column(Integer)
    slayer = Column(Integer)
    farming = Column(Integer)
    runecraft = Column(Integer)
    hunter = Column(Integer)
    construction = Column(Integer)
    league = Column(Integer)
    bounty_hunter_hunter = Column(Integer)
    bounty_hunter_rogue = Column(Integer)
    cs_all = Column(Integer)
    cs_beginner = Column(Integer)
    cs_easy = Column(Integer)
    cs_medium = Column(Integer)
    cs_hard = Column(Integer)
    cs_elite = Column(Integer)
    cs_master = Column(Integer)
    lms_rank = Column(Integer)
    soul_wars_zeal = Column(Integer)
    abyssal_sire = Column(Integer)
    alchemical_hydra = Column(Integer)
    barrows_chests = Column(Integer)
    bryophyta = Column(Integer)
    callisto = Column(Integer)
    cerberus = Column(Integer)
    chambers_of_xeric = Column(Integer)
    chambers_of_xeric_challenge_mode = Column(Integer)
    chaos_elemental = Column(Integer)
    chaos_fanatic = Column(Integer)
    commander_zilyana = Column(Integer)
    corporeal_beast = Column(Integer)
    crazy_archaeologist = Column(Integer)
    dagannoth_prime = Column(Integer)
    dagannoth_rex = Column(Integer)
    dagannoth_supreme = Column(Integer)
    deranged_archaeologist = Column(Integer)
    general_graardor = Column(Integer)
    giant_mole = Column(Integer)
    grotesque_guardians = Column(Integer)
    hespori = Column(Integer)
    kalphite_queen = Column(Integer)
    king_black_dragon = Column(Integer)
    kraken = Column(Integer)
    kreearra = Column(Integer)
    kril_tsutsaroth = Column(Integer)
    mimic = Column(Integer)
    nightmare = Column(Integer)
    obor = Column(Integer)
    sarachnis = Column(Integer)
    scorpia = Column(Integer)
    skotizo = Column(Integer)
    Tempoross = Column(Integer, nullable=False)
    the_gauntlet = Column(Integer)
    the_corrupted_gauntlet = Column(Integer)
    theatre_of_blood = Column(Integer)
    theatre_of_blood_hard = Column(Integer)
    thermonuclear_smoke_devil = Column(Integer)
    tzkal_zuk = Column(Integer)
    tztok_jad = Column(Integer)
    venenatis = Column(Integer)
    vetion = Column(Integer)
    vorkath = Column(Integer)
    wintertodt = Column(Integer)
    zalcano = Column(Integer)
    zulrah = Column(Integer)

    Player = relationship('Player')
