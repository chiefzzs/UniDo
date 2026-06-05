#!/usr/bin/env python3
"""
AI Agent System - Development Mode Launch Script

启动L4网关层，提供HTTP API和WebSocket服务。

Usage:
    python run.py [--host HOST] [--port PORT] [--dev]
    
Options:
    --host HOST    服务器绑定地址 (默认: 0.0.0.0)
    --port PORT    服务器端口 (默认: 8000)
    --dev          开发模式，启用热重载
"""

import argparse
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    parser = argparse.ArgumentParser(description="AI Agent System - Development Mode")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--dev", action="store_true", default=True, help="Development mode")
    args = parser.parse_args()
    
    print("Starting AI Agent System in Development Mode")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Hot Reload: {args.dev}")
    print("=" * 50)
    
    import uvicorn
    
    # 使用导入字符串方式启动，支持热重载
    uvicorn.run(
        "services.L4_gateway.L4a_http_gateway.api_server:create_app",
        host=args.host,
        port=args.port,
        reload=args.dev,
        reload_dirs=["src"],
        factory=True
    )

if __name__ == "__main__":
    main()