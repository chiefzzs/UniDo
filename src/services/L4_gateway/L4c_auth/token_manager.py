"""
Token Manager - Token管理器

提供JWT token的生成和验证功能。
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt

class TokenManager:
    """Token管理器"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def generate_token(self, username: str, expires_in: int = 3600) -> str:
        """生成JWT token
        
        Args:
            username: 用户名
            expires_in: token有效期（秒），默认为1小时
            
        Returns:
            JWT token字符串
        """
        payload = {
            "sub": username,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, ignore_expiration: bool = False) -> Optional[Dict[str, Any]]:
        """验证JWT token
        
        Args:
            token: JWT token字符串
            ignore_expiration: 是否忽略过期时间
            
        Returns:
            解码后的payload，如果验证失败返回None
        """
        try:
            options = {"verify_exp": not ignore_expiration}
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options=options)
        except jwt.InvalidTokenError:
            return None