# -*- coding: utf-8 -*-
"""
快速启动 visualization.html 的 Python 脚本。
该脚本会启动一个本地 HTTP 服务器并在默认浏览器中打开 visualization.html 页面。
"""
import webbrowser
import threading
import time
import os
import http.server
import socketserver

# 设置服务器端口
PORT = 8000

# 获取当前目录
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# 切换到 HTML 文件所在目录
os.chdir(DIRECTORY)

# 定义服务器类
Handler = http.server.SimpleHTTPRequestHandler


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


# 启动服务器的函数
def start_server():
    with ReusableTCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    import socket

    # 检查端口是否被占用
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('localhost', PORT)) == 0:
            print(f"Port {PORT} is occupied. Trying to find a new port...")
            PORT = 8081  # 尝试使用新端口

    # 创建并启动服务器线程
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    # 等待服务器启动
    time.sleep(1)

    # 打开浏览器访问 visualization.html
    webbrowser.open(f'http://localhost:{PORT}/visualization.html')

    # 提示用户如何退出
    input('Press Enter to stop the server...')