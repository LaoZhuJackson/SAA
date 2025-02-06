import sys
from pyupdater.client import Client

APP_NAME = "MyApp"
UPDATE_URL = "https://your-update-server.com/updates/"  # 你的更新服务器

def check_for_update():
    # https://www.pyupdater.org/commands/
    client = Client(APP_NAME, UPDATE_URL)
    client.refresh()
    if client.update_ready():
        client.download()
        client.extract_restart()

if __name__ == "__main__":
    check_for_update()
    print("Hello, this is MyApp!")
