from typing import Generator, Dict, Any

class StreamOutput:
    def __init__(self):
        pass
    
    def process_stream(self, stream_generator: Generator[str, None, None]) -> Generator[Dict[str, Any], None, None]:
        for chunk in stream_generator:
            yield {
                "type": "stream_chunk",
                "content": chunk,
                "is_complete": False
            }
        yield {
            "type": "stream_chunk",
            "content": "",
            "is_complete": True
        }
