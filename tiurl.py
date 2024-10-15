import sys
import re
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton


class ImageExtractor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 输入文本框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在此输入HTML代码...")
        layout.addWidget(self.input_text)

        # 处理按钮
        self.process_button = QPushButton("处理")
        self.process_button.clicked.connect(self.process_html)
        layout.addWidget(self.process_button)

        # 输出文本框
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("处理结果将显示在这里...")
        layout.addWidget(self.output_text)

        self.setLayout(layout)
        self.setWindowTitle('HTML图片提取器')
        self.setGeometry(300, 300, 800, 600)

    def process_html(self):
        html = self.input_text.toPlainText()

        # 提取所有<img>标签的src属性
        img_urls = re.findall(r'<img.*?src=["\'](.+?)["\']', html, re.IGNORECASE)

        # 从URL中提取clientCacheKey参数的值
        results = []
        for url in img_urls:
            match = re.search(r'clientCacheKey=(.+?)\.jpg', url)
            if match:
                results.append(match.group(1))

        # 过滤带animatedV5内容
        results = [item for item in results if 'animatedV5' not in item]
        results = [item.split("_")[0] if "_" in item else item for item in results]
        results = ["https://www.kuaishou.com/short-video/"+item+"/" for item in results]

        # 将结果显示在输出文本框中
        print(f"总条目{len(results)}条")
        self.output_text.setPlainText('\n'.join(results))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageExtractor()
    ex.show()
    sys.exit(app.exec_())