import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from pydantic import DirectoryPath
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv(find_dotenv(".env"))


class Config(BaseSettings):

    model_config = SettingsConfigDict(env_prefix='SUIL_')

    # Directories
    base_dir: DirectoryPath = os.path.dirname(os.path.realpath(__file__))

    @property
    def data_dir(self):
        return Path(self.base_dir) / 'data'

    @property
    def facts_dir(self):
        return Path(self.base_dir) / 'facts'

    @property
    def modules_dir(self):
        return Path(self.base_dir) / 'modules'

    @property
    def hierarchy_file(self):
        return self.data_dir / 'common.yaml'

    @property
    def roles_dir(self):
        return self.data_dir / 'roles'

    @property
    def nodes_dir(self):
        return self.data_dir / 'nodes'


cfg = Config()
