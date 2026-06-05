"""
L2b Memory and State Management - API Request Log Service

专门处理 RESTful API 请求/响应日志的服务
"""

import json
from typing import Dict, Any, Optional
from .base_log_service import BaseLogService
from .api_log_models import APIRequestLog


class APIRequestLogService(BaseLogService):
    """API请求日志服务"""
    
    COLLECTION_NAME = "api_requests"
    
    def __init__(self):
        super().__init__()
    
    def save_api_request(self, method: str, path: str, client_id: str = "", 
                         query_params: Dict[str, Any] = None, body: Any = None,
                         headers: Dict[str, str] = None) -> str:
        """
        保存API请求日志
        
        :param method: HTTP方法 (GET, POST, PUT, DELETE等)
        :param path: 请求路径
        :param client_id: 客户端ID
        :param query_params: 查询参数
        :param body: 请求体
        :param headers: 请求头
        :return: 请求ID
        """
        import uuid
        request_id = f"req-{uuid.uuid4().hex[:16]}"
        
        # 序列化请求体
        body_str = None
        if body is not None:
            try:
                body_str = json.dumps(body, ensure_ascii=False)
            except:
                body_str = str(body)
        
        log = APIRequestLog(
            log_id=self.generate_log_id("api"),
            request_id=request_id,
            client_id=client_id,
            method=method,
            path=path,
            query_params=query_params or {},
            body=body_str,
            headers=headers or {}
        )
        
        self._save_log(self.COLLECTION_NAME, log.to_dict())
        return request_id
    
    def update_api_response(self, request_id: str, status_code: int, 
                           response_body: Any = None, response_time: float = None,
                           error_message: str = None) -> bool:
        """
        更新API响应日志
        
        :param request_id: 请求ID
        :param status_code: 响应状态码
        :param response_body: 响应体
        :param response_time: 响应时间（毫秒）
        :param error_message: 错误消息
        :return: 是否更新成功
        """
        logs = self._get_logs(self.COLLECTION_NAME, {"request_id": request_id})
        
        if not logs:
            return False
        
        log_data = logs[0]
        log_data['status_code'] = status_code
        
        # 序列化响应体
        if response_body is not None:
            try:
                log_data['response_body'] = json.dumps(response_body, ensure_ascii=False)
            except:
                log_data['response_body'] = str(response_body)
        
        if response_time is not None:
            log_data['response_time'] = response_time
        
        if error_message is not None:
            log_data['error_message'] = error_message
        
        self._save_log(self.COLLECTION_NAME, log_data)
        return True
    
    def get_api_requests(self, filters: Dict[str, Any] = None) -> list:
        """
        获取API请求日志列表
        
        :param filters: 过滤条件
        :return: 日志列表
        """
        return self._get_logs(self.COLLECTION_NAME, filters)
    
    def get_api_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个API请求日志
        
        :param request_id: 请求ID
        :return: 日志详情
        """
        logs = self._get_logs(self.COLLECTION_NAME, {"request_id": request_id})
        return logs[0] if logs else None


# 全局单例
_api_request_log_service: Optional[APIRequestLogService] = None


def get_api_request_log_service() -> APIRequestLogService:
    """获取API请求日志服务的单例实例"""
    global _api_request_log_service
    if _api_request_log_service is None:
        _api_request_log_service = APIRequestLogService()
    return _api_request_log_service
