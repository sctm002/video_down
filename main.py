import sys
import os
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (QApplication, QMainWindow, QToolBar, QTextEdit,
                             QAction, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QSplitter)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
from tool import DownloadWorker, yibusleep
import time
from datetime import datetime



# 批量下载视频程序
class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.directory = ".\\"
        # 被拦截时等待时间，每拦截一次等待时间加长，成功后归0
        self.lanjie_time = 0
        self.zong = 0

        self.setWindowTitle('视频源批处理提取器')
        self.setGeometry(100, 100, 1280, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.splitter = QSplitter()
        self.layout.addWidget(self.splitter)

        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.splitter.addWidget(self.left_widget)

        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("在此处输入URL，每行一个。")
        self.left_layout.addWidget(self.url_input)

        self.browser = QWebEngineView()
        self.splitter.addWidget(self.browser)

        self.splitter.setSizes([400, 880])  # Set initial sizes of the splitter

        self.page = QWebEnginePage()
        self.browser.setPage(self.page)

        self.page.profile().setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        navtb = QToolBar()
        self.addToolBar(navtb)

        extract_action = QAction('提取视频源', self)
        extract_action.triggered.connect(self.extract_video_sources)
        navtb.addAction(extract_action)

        self.urls = []
        self.current_url_index = 0
        self.output_file = ""

    # 处理批量链接
    def extract_video_sources(self):
        self.urls = [url.strip() for url in self.url_input.toPlainText().split('\n') if url.strip()]
        self.urls = [item for item in self.urls if item.startswith("http")]
        self.zong = len(self.urls)
        if not self.urls:
            QMessageBox.warning(self, "无链接", "请至少输入一条链接")
            return
        directory = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if not directory:
            return
        self.directory = directory
        self.output_file = os.path.join(directory, "url.txt")
        self.current_url_index = 0
        self.process_next_url()

    # 打开下一个目标地址
    def process_next_url(self):
        if self.current_url_index < len(self.urls):
            url = self.urls[self.current_url_index]
            self.browser.setUrl(QUrl(url))
            self.browser.loadFinished.connect(self.on_page_load_finished)
        else:
            QMessageBox.information(self, "提示：", "所有链接都运行完成。")

    # 加载完成后运行
    def on_page_load_finished(self):
        self.browser.loadFinished.disconnect(self.on_page_load_finished)
        self.get_video_source()

    # 查找视频地址
    def get_video_source(self):
        js = """
        (function() {
            var video = document.querySelector('video.player-video[data-v-4c895b0a]');
            return video ? video.src : '';
        })()
        """
        self.page.runJavaScript(js, self.save_video_source)

    # 存储视频地址
    def save_video_source(self, src):
        if src:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(f"{self.urls[self.current_url_index]}\n{src}\n\n")
            # 下载视频
            stamp = int(time.time()*1000)
            rqi = datetime.now().strftime("%Y%m%d")
            out_path = f"{rqi}-{stamp}.mp4"
            out_path = os.path.join(self.directory, out_path)
            # 循环增加i
            print(f"存储视频链接 URL: {self.urls[self.current_url_index]}")
            self.lanjie_time = 5
            self.current_url_index += 1
            # 异步下载
            self.worker = DownloadWorker(src, out_path)
            self.worker.finished.connect(self.down_ok)
            self.worker.start()
        else:
            print(f"未找到视频链接 URL: {self.urls[self.current_url_index]}")
            # raise Exception("未找到视频链接，请检测是否有验证码。")
            self.lanjie_time += (60+int(self.lanjie_time//2))
            print(f"拦截等待{self.lanjie_time}秒。")
        self.dengdai = yibusleep(self.lanjie_time)
        self.dengdai.finished.connect(self.process_next_url)
        self.dengdai.start()

    # 异步下载回调
    def down_ok(self):
        print(f"ID{self.current_url_index}/{self.zong}下载完成。")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Browser()
    window.show()
    sys.exit(app.exec_())





