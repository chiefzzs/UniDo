import os
from .file_storage import FileStorage
from typing import Optional


class StorageFactory:
    _instance: Optional[FileStorage] = None

    @classmethod
    def create(cls, base_path: str = None, env: str = None) -> FileStorage:
        if base_path is None:
            base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), 'src', 'data')

        if env is None:
            env = os.environ.get('STORAGE_ENV', 'dev')

        cls._instance = FileStorage(base_path, env)
        return cls._instance

    @classmethod
    def get_instance(cls) -> Optional[FileStorage]:
        return cls._instance
