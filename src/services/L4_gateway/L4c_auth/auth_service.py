"""
Auth Service - 认证服务

提供用户认证功能。
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt

class AuthService:
    """认证服务"""
    
    def __init__(self, secret_key: str = "secret_key", algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_manager = TokenManager(secret_key, algorithm)
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """认证用户并返回JWT token
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            JWT token字符串，如果认证失败返回None
        """
        # 在实际应用中，应该从数据库验证用户凭证
        # 这里简化处理，接受任何非空用户名和密码
        if username and password:
            return self.token_manager.generate_token(username)
        return None
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT token
        
        Args:
            token: JWT token字符串
            
        Returns:
            解码后的payload，如果验证失败返回None
        """
        return self.token_manager.verify_token(token)
    
    def refresh_token(self, token: str) -> Optional[str]:
        """刷新JWT token
        
        Args:
            token: 过期的JWT token
            
        Returns:
            新的JWT token字符串，如果刷新失败返回None
        """
        payload = self.token_manager.verify_token(token, ignore_expiration=True)
        if payload:
            username = payload.get("sub")
            if username:
                return self.token_manager.generate_token(username)
        return None