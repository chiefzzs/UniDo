from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional, List


class BaseAdapter(ABC):
    def __init__(self, api_address: str, api_key: str, model_name: str):
        self.api_address = api_address.rstrip('/')
        self.api_key = api_key
        self.model_name = model_name

    @abstractmethod
    def build_request_payload(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def parse_stream_chunk(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def get_api_endpoint(self) -> str:
        return f"{self.api_address}/chat/completions"
