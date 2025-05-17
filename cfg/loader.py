import logging
import os
from pydantic import ValidationError



from .bot import BotSettings
from .srv import SrvSettings
from .database import DatabaseSettings

logger = logging.getLogger(__name__)
env_bot_path = '.env_bot'
env_srv_path = '.env_srv'
env_db_path = '.env_db'



def cfg_bot():
    logger.info('>>> Inceput de initializare configurari BOT - .env_srv <<<')

    if not os.path.exists(env_bot_path):
        logger.error("The .env_srv file does not exist at the provided path.")

    if os.stat(env_bot_path).st_size == 0:
        logger.error("The .env_srv file is empty.")

    try:
        print("===========================")
        logger.info('>>> Initializarea obiectului BOT-ului inceput<<<')
        tg_bot = BotSettings(_env_file=env_bot_path)
        logger.info('>>> Initializarea obiectului BOT-ului finalizat fara erori<<<')
        print("===========================")
    except (ValidationError, ValueError) as e:
        if isinstance(e, ValidationError):
            print("ValidationError: ",e)
            logger.error("ValidationError in load_config.BotSettings: ")
        elif isinstance(e, ValueError):
            print("ValueError: ",e)
            logger.error("ValueError in load_config.BotSettings: ")
        config = None
        return config

    return tg_bot.dict()

# ex cfg_token
def cfg_srv():

    logger.info('>>> Inceput de initializare configurari BOT - .env_srv <<<')

    if not os.path.exists(env_srv_path):
        logger.error("The .env_srv file does not exist at the provided path.")

    if os.stat(env_srv_path).st_size == 0:
        logger.error("The .env_srv file is empty.")

    try:
        print("===========================")
        logger.info('>>> Initializarea obiectului srv_token inceput<<<')
        srv_token = SrvSettings(_env_file=env_srv_path)
        logger.info('>>> Initializarea obiectului srv_token finalizat fara erori<<<')
        print("===========================")
    except (ValidationError, ValueError) as e:
        if isinstance(e, ValidationError):
            print("ValidationError: ",e)
            logger.error("ValidationError in load_config.BotSettings: ")
        elif isinstance(e, ValueError):
            print("ValueError: ",e)
            logger.error("ValueError in load_config.BotSettings: ")
        config = None
        return config

    return srv_token.dict()



def cfg_db():

    try:
        print("===========================")
        logger.info('>>> Initializarea setarilor DB pentru BOT-ului inceput<<<')
        print('>>> Initializarea setarilor DB pentru BOT-ului inceput<<<')
        database_settings = DatabaseSettings(_env_file=env_db_path)
        db_settings_url = database_settings.db_url

        print(f"LOADER db_settings_url = {db_settings_url}")

        logger.info('>>> Initializarea setarilor DB pentru BOT-ului finalizat fara erori<<<')
        print("===========================")
    except (ValidationError, ValueError) as e:
        if isinstance(e, ValidationError):
            if e.errors()[0]['type'] != 'value_error':
                print("*********")
                for er in e.errors():
                    print(f"ValidationError in {er['loc'][0]} => {er['type']}")
                    logger.error("ValidationError in load_config.DatabaseSettings. %s => %s error", er['loc'][0], er['type'])
            else:
                logger.error("True True")
        elif isinstance(e, ValueError):
            print("ValueError: ",e)
            logger.error("ValueError in load_config.DatabaseSettings: ")
        db_settings_url = None

    return db_settings_url




