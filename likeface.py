import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTextEdit, QFileDialog, QListWidget, QListWidgetItem
from PyQt5.QtWebEngineWidgets import QWebEngineView
from bs4 import BeautifulSoup
import os
from PyQt5.QtCore import Qt,QUrl, QDir, QEventLoop, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PIL import Image
import mimetypes
from urllib.parse import urlparse, parse_qs
import time
from liketool import FaceComparator
import cv2



# 图片下载拦截器
class ImageInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.img_name = []  # 用于存储已下载的图片名称
        self.network_manager = QNetworkAccessManager()

    def is_image_url(self, url):
        # 检查URL是否可能是图片
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        query = parsed_url.query.lower()
        # 检查常见的图片扩展名
        if any(path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
            return True
        # 检查URL中是否包含图片相关的关键词
        if 'image' in path or 'img' in path or 'photo' in path:
            return True
        # 检查查询参数中是否指定了图片格式
        if 'format=jpg' in query or 'format=png' in query or 'type=image' in query:
            return True
        return False

    # 文件名处理
    def extract_filename_from_url(self, url):
        # 解析URL
        parsed_url = urlparse(url)
        # 检查是否存在clientCacheKey参数
        query_params = parse_qs(parsed_url.query)
        if 'clientCacheKey' in query_params:
            # 如果存在clientCacheKey参数，使用它作为文件名
            return query_params['clientCacheKey'][0]
        # 如果不存在clientCacheKey，使用原来的逻辑
        file_name = os.path.basename(parsed_url.path)
        if not file_name:
            file_name = url.split('/')[-1]
        if not file_name or '.' not in file_name:
            file_name = f"image_{len(self.img_name)}.jpg"
        return file_name

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        if self.is_image_url(url):
            file_name = self.extract_filename_from_url(url)
            if file_name not in self.img_name:
                self.img_name.append(file_name)
                QDir().mkpath('./cache/')  # 确保缓存目录存在
                file_path = os.path.join('./cache/', file_name)
                # 使用 PyQt 的网络访问管理器下载图片
                request = QNetworkRequest(QUrl(url))
                reply = self.network_manager.get(request)
                loop = QEventLoop()
                reply.finished.connect(loop.quit)
                loop.exec_()
                if reply.error() == QNetworkReply.NoError:
                    content_type = reply.header(QNetworkRequest.ContentTypeHeader)
                    if content_type and content_type.startswith('image/'):
                        with open(file_path, 'wb') as f:
                            f.write(reply.readAll())
                        print(f"图片已保存: {file_path}")
                    else:
                        print(f"非图片内容: {url}")
                else:
                    print(f"下载图片失败: {url}, 错误: {reply.errorString()}")
                reply.deleteLater()

# 单独的图片显示区域控件
class ClickableListWidget(QListWidget):
    itemClicked = pyqtSignal(str)  # 自定义信号，用于发送被点击项的 URL
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        item = self.itemAt(event.pos())
        if item:
            url = item.data(Qt.UserRole)  # 获取存储在项中的 URL
            self.itemClicked.emit(url)  # 发送信号

# 主UI界面
class Browser(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.interceptor = ImageInterceptor()
        self.web_view.page().profile().setRequestInterceptor(self.interceptor)
        self.old_img = []
        self.this_img = ""

    def initUI(self):
        self.setWindowTitle('MIR T 浏览器')
        self.setGeometry(100, 100, 1680, 720)

        # Main layout
        main_layout = QVBoxLayout()

        # Top bar with URL input and Go button
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(10, 0, 0, 0)
        self.url_input = QLineEdit()
        self.url_input.setFixedHeight(20)
        self.url_input.setText("https://www.kuaishou.com/samecity")
        go_button = QPushButton('Go')
        go_button.setFixedHeight(20)
        go_button.clicked.connect(self.navigate)
        top_bar.addWidget(self.url_input)
        top_bar.addWidget(go_button)

        main_layout.addLayout(top_bar)

        # Content area (split into left and right)
        content_layout = QHBoxLayout()

        # Left panel
        left_panel = QVBoxLayout()
        parse_button = QPushButton('清空')
        parse_button.setFixedHeight(30)
        parse_button.clicked.connect(self.del_cacke)

        # 图片列表区域
        self.image_list = ClickableListWidget()
        self.image_list.itemClicked.connect(self.copy_url_to_clipboard)
        self.image_list.setIconSize(QSize(206, 340))

        # 图片选择文本框
        self.image_path = QLineEdit()
        self.image_path.setPlaceholderText("选择或拖放图片...")
        self.image_path.setReadOnly(True)
        self.image_path.mousePressEvent = self.select_image

        like_button = QPushButton('相似度')
        like_button.setFixedHeight(30)
        like_button.clicked.connect(self.like_face)

        mp4toimg_button = QPushButton('视频分解为图片')
        mp4toimg_button.setFixedHeight(30)
        mp4toimg_button.clicked.connect(self.mp4toimg_def)

        left_panel.addWidget(parse_button)
        left_panel.addWidget(self.image_list)
        left_panel.addWidget(self.image_path)
        left_panel.addWidget(like_button)
        left_panel.addWidget(mp4toimg_button)

        # Create a container widget for the left panel
        left_container = QWidget()
        left_container.setLayout(left_panel)
        left_container.setFixedWidth(360)

        # Web view (right panel)
        self.web_view = QWebEngineView()

        # Add left and right panels to the content layout
        content_layout.addWidget(left_container)
        content_layout.addWidget(self.web_view)

        # Add content layout to main layout
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

    # 选择本地图片
    def select_image(self, event):
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(self, "选择图片", "", "图片文件 (*.png *.jpg *.bmp *.mp4)")
        if image_path:
            self.image_path.setText(image_path)
            self.this_img = image_path
            print("image_path:", image_path)

    # 提取页面图片
    def navigate(self):
        url = self.url_input.text()
        if not url.startswith('http'):
            url = 'http://' + url
        self.web_view.setUrl(QUrl(url))
        # self.web_view.loadFinished.connect(self.process_images)

    # 清除所有缓存图
    def del_cacke(self):
        cache_dir = './cache/'
        path_list = os.listdir(cache_dir)
        for img_name in path_list:
            img_path = os.path.join(cache_dir, img_name)
            try:
                os.remove(img_path)
                print(f"删除小图片: {img_path}")
            except Exception as e:
                print(f"处理图片时出错: {img_path}, 错误: {str(e)}")

    # 删除小图
    def process_images(self):
        # 处理完成后，删除小图片
        cache_dir = './cache/'
        path_list = os.listdir(cache_dir)
        for img_name in path_list:
            img_path = os.path.join(cache_dir, img_name)
            try:
                if img_path.endswith(".svg"):
                    os.remove(img_path)
                    print(f"删除SVG文件: {img_path}")
                    continue
                with Image.open(img_path) as img:
                    width, height = img.size
                # 关闭图片后再检查大小并删除
                if width < 201 and height < 201:
                    time.sleep(0.1)  # 短暂延时，确保文件被完全释放
                    os.remove(img_path)
                    print(f"删除小图片: {img_path}")
            except Exception as e:
                print(f"处理图片时出错: {img_path}, 错误: {str(e)}")
        print("图片处理完成")

    def like_face(self):
        # 先清除小图
        self.process_images()
        if not self.this_img:
            print("对比图片不存在，请先选择图片。")
            return
        if not os.path.exists(self.this_img):
            print("对比图片未找到，请确认图片路径。")
            return
        mb_imgpath = os.listdir("./cache")
        mb_imgpath = [item for item in mb_imgpath if item.endswith('.jpg') or item.endswith('.png')]
        mb_imgpath = [os.path.join("./cache",item) for item in mb_imgpath]
        # 过滤已计算过图片self.old_img
        mb_imgpath = [item for item in mb_imgpath if item not in self.old_img]
        self.old_img = self.old_img + mb_imgpath
        # 相似度计算
        comparator = FaceComparator()
        similarity = comparator.compare_faces(self.this_img, mb_imgpath)
        print("similarity:", similarity)
        # 清空现有的项目
        # self.image_list.clear()
        # # 找出最大的数字及其索引
        # max_index = similarity.index(max(similarity))
        # max_score = similarity[max_index]
        # max_img_path = mb_imgpath[max_index]
        # 使用列表推导式筛选出相似度大于阈值的项
        high_similarity = [(path, score) for score, path in zip(similarity, mb_imgpath) if score > 0.68]
        # 按相似度降序排序
        high_similarity.sort(key=lambda x: x[1], reverse=True)
        for path_zu in high_similarity:
            # 创建一个新的 QListWidgetItem
            item = QListWidgetItem()
            # 设置图标（图片）
            icon = QIcon(QPixmap(path_zu[0]).scaled(206, 340, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            item.setIcon(icon)
            # 拼接实际地址
            base_name = os.path.basename(path_zu[0])
            base_name = os.path.splitext(base_name)[0]
            # 检查是否含有下划线
            if '_' in base_name:
                # 如果有下划线，取下划线之前的内容
                processed_name = base_name.split('_')[0]
            else:
                # 如果没有下划线，使用整个文件名（不包含扩展名）
                processed_name = base_name
            # 生成新的URL
            base_url = "https://www.kuaishou.com/short-video/" + processed_name +"/"
            # 设置文本
            item.setText(f"Similarity: {path_zu[1]:.4f}")
            item.setData(Qt.UserRole, base_url)
            # 将项目添加到列表中
            self.image_list.addItem(item)

    # 复制图片主页方法
    def copy_url_to_clipboard(self, url):
        QApplication.clipboard().setText(url)
        print(f"复制地址到剪切板: {url}")

    # 将MP4分解为图片，每秒为3帧
    def mp4toimg_def(self):
        if not self.this_img.endswith('.mp4'):
            print("传入的不是视频文件。")
            return
        # 确保输出目录存在
        output_dir = './mp4img'
        os.makedirs(output_dir, exist_ok=True)
        # 打开视频文件
        video = cv2.VideoCapture(self.this_img)
        # 获取视频的帧率
        fps = video.get(cv2.CAP_PROP_FPS)
        # 计算每隔多少帧保存一次图片
        frame_interval = round(fps / 3)
        # 初始化帧计数器
        frame_count = 0
        while True:
            # 读取一帧
            success, frame = video.read()
            # 如果读取失败，说明视频已经结束
            if not success:
                break
            # 每隔 frame_interval 帧保存一次图片
            if frame_count % frame_interval == 0:
                # 生成输出文件名
                output_filename = os.path.join(output_dir, f'frame_{frame_count:06d}.jpg')
                # 保存图片
                cv2.imwrite(output_filename, frame)
            # 增加帧计数器
            frame_count += 1
        # 释放视频对象
        video.release()
        print(f"处理完成。共保存了 {frame_count // frame_interval} 张图片到 {output_dir} 目录。")









if __name__ == '__main__':
    app = QApplication(sys.argv)
    browser = Browser()
    browser.show()
    sys.exit(app.exec_())





