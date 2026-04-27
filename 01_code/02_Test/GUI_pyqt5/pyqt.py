# import sys
# import os
# from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
# from PyQt5.QtGui import QPixmap
# from PyQt5.QtCore import Qt

# class ImageWindow(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("PyQt5 Folder Image Loader")
#         self.resize(800, 600)

#         self.base_folder = "assets"
#         self.sequence_name = "idle"   # 여기 폴더명을 바꾸면 됨

#         self.label = QLabel("No Image")
#         self.label.setAlignment(Qt.AlignCenter)

#         layout = QVBoxLayout()
#         layout.addWidget(self.label)
#         self.setLayout(layout)

#         self.load_first_image()

#     def load_first_image(self):
#         folder_path = os.path.join(self.base_folder, self.sequence_name)

#         if not os.path.exists(folder_path):
#             self.label.setText(f"Folder not found:\n{folder_path}")
#             return

#         files = sorted(
#             f for f in os.listdir(folder_path)
#             if f.lower().endswith((".png", ".jpg", ".jpeg"))
#         )

#         if not files:
#             self.label.setText(f"No image files in:\n{folder_path}")
#             return

#         first_image_path = os.path.join(folder_path, files[0])
#         pixmap = QPixmap(first_image_path)

#         if pixmap.isNull():
#             self.label.setText(f"Failed to load image:\n{first_image_path}")
#             return

#         self.label.setPixmap(pixmap)

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = ImageWindow()
#     window.show()
#     sys.exit(app.exec_())


import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer



class SequenceViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Sequence Viewer")
        self.resize(800, 600)

        self.base_folder = "assets"
        self.sequence_name = "idle"

        self.image_paths = []
        self.current_index = 0

        self.label = QLabel("No Image")
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.load_sequence(self.sequence_name)
        # self.show_current_image()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_current_image)
        # 42 = 1 sec(1000) / 24
        self.timer.start(42)

    def load_sequence(self, folder_name):
        folder_path = os.path.join(self.base_folder, folder_name)

        if not os.path.isdir(folder_path):
            self.image_paths = []
            self.label.setText(f"Folder not found:\n{folder_path}")
            return

        files = sorted(
            f for f in os.listdir(folder_path)
            if f.lower().endswith(".png")
        )

        self.image_paths = [os.path.join(folder_path, f) for f in files]
        # self.current_index = 0
        self.sequence_name = folder_name

        if not self.image_paths:
            self.label.setText(f"No PNG files in:\n{folder_path}")

    def show_current_image(self):
        if not self.image_paths:
            return

        image_path = self.image_paths[self.current_index]
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            self.label.setText(f"Failed to load:\n{image_path}")
            return

        scaled = pixmap.scaled(
            self.label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.label.setPixmap(scaled)
        
        self.current_index += 1
        if self.current_index >= len(self.image_paths):
            self.current_index = 0

    def change_sequence(self, folder_name):
        self.current_index = 0
        self.load_sequence(folder_name)
        self.show_current_image()

    def resizeEvent(self, event):
        self.show_current_image()
        super().resizeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SequenceViewer()
    window.show()

    # window.change_sequence("smile")

    sys.exit(app.exec_())