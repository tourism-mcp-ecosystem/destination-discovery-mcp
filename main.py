#!/usr/bin/env python3
"""
目的地发现MCP服务器 - 主启动入口
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server import DestinationDiscoveryServer
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="目的地发现MCP服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        示例:
  %(prog)s                    # 默认在 0.0.0.0:8000 启动
  %(prog)s --port 8080        # 在端口 8080 启动
  %(prog)s --host 127.0.0.1   # 在本地回环地址启动
        """
    )
    
    parser.add_argument("--host", default="0.0.0.0",
                       help="服务器监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000,
                       help="服务器监听端口 (默认: 8000)")
    parser.add_argument("--debug", action="store_true",
                       help="启用调试模式")
    
    args = parser.parse_args()
    
    # 创建并启动服务器
    server = DestinationDiscoveryServer()
    
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        print(f"调试模式已启用，服务器将在 http://{args.host}:{args.port} 启动")
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"服务器启动失败: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()