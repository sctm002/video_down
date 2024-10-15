from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QEventLoop
import sys

def get_html_from_url(url):
    app = QApplication(sys.argv)
    view = QWebEngineView()
    loop = QEventLoop()

    view.loadFinished.connect(loop.quit)
    view.load(QUrl(url))
    loop.exec_()

    html = view.page().toHtml(lambda x: html_callback(x, loop))
    loop.exec_()

    view.close()
    app.quit()

    return html

def html_callback(html_str, loop):
    global html
    html = html_str
    loop.quit()

# 使用示例
if __name__ == "__main__":
    url = "https://www.qidian.com/chapter/1041604040/806905398/"
    html_content = get_html_from_url(url)
    print(html_content)


