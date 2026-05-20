from typing import Dict, Any, List, Optional
from services.L2_domain.L2a_project_config.model_config_service import ModelConfigService

class ModelConfig:
    def __init__(self):
        self.model_config_service = ModelConfigService()
    
    def create(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        model = self.model_config_service.create_model_config(
            name=config_data.get("name"),
            model_name=config_data.get("model_name", "qwen-7b"),
            api_type=config_data.get("api_type", "cloud"),
            api_address=config_data.get("api_address", "https://api.example.com"),
            api_key=config_data.get("api_key", ""),
            parameters=config_data.get("parameters", {})
        )
        return model.to_dict()
    
    def get(self, config_id: str) -> Optional[Dict[str, Any]]:
        model = self.model_config_service.get_model_config(config_id)
        return model.to_dict() if model else None
    
    def update(self, config_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        model = self.model_config_service.update_model_config(
            config_id=config_id,
            **update_data
        )
        return model.to_dict() if model else None
    
    def list(self) -> List[Dict[str, Any]]:
        from services.L2_domain.L2a_project_config.models import ModelConfig as ModelConfigModel
        all_configs = self.model_config_service.persistence.list('model_configs')
        return [ModelConfigModel.from_dict(c).to_dict() for c in all_configs]
    
    def delete(self, config_id: str) -> Dict[str, bool]:
        all_configs = self.model_config_service.persistence.list('model_configs')
        new_configs = [c for c in all_configs if c.get('config_id') != config_id]
        if len(new_configs) != len(all_configs):
            self.model_config_service.persistence._write_all('model_configs', new_configs)
            return {"success": True}
        return {"success": False}
