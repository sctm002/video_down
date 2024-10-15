import time

import requests
import os
from tqdm import tqdm
from PyQt5.QtCore import QThread, pyqtSignal



def download_mp4(url, output_path):
    # 发送 GET 请求到视频 URL
    response = requests.get(url, stream=True)

    # 确保请求成功
    response.raise_for_status()

    # 获取文件大小（如果服务器提供）
    file_size = int(response.headers.get('Content-Length', 0))

    # 打开文件准备写入
    with open(output_path, 'wb') as file, tqdm(
            desc=output_path,
            total=file_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
    ) as progress_bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            progress_bar.update(size)


class DownloadWorker(QThread):
    finished = pyqtSignal()

    def __init__(self, url, path):
        super().__init__()
        self.url = url
        self.path = path

    def run(self):
        response = requests.get(self.url)
        with open("video.mp4", "wb") as f:
            f.write(response.content)

        download_mp4(self.url, self.path)
        self.finished.emit()


# 异步等待函数
class yibusleep(QThread):
    finished = pyqtSignal()
    def __init__(self, miao):
        super().__init__()
        self.miao = miao

    def run(self):
        time.sleep(self.miao)
        self.finished.emit()
