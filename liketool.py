import dlib
import numpy as np
from skimage import io
from typing import List


class FaceComparator:
    def __init__(self):
        # 加载 Dlib 的人脸检测器和特征提取模型
        self.detector = dlib.get_frontal_face_detector()
        self.sp = dlib.shape_predictor('./model/shape_predictor_68_face_landmarks.dat')
        self.facerec = dlib.face_recognition_model_v1('./model/dlib_face_recognition_resnet_model_v1.dat')

    def __del__(self):
        # 在类被销毁时释放资源
        del self.detector
        del self.sp
        del self.facerec

    @staticmethod
    def get_largest_face(faces, img_shape):
        if not faces:
            return None
        # 计算每个人脸的面积
        areas = [((face.right() - face.left()) * (face.bottom() - face.top())) / (img_shape[0] * img_shape[1]) for face
                 in faces]
        # 返回面积最大的人脸
        return faces[np.argmax(areas)]

    def get_face_descriptor(self, img, face):
        shape = self.sp(img, face)
        return self.facerec.compute_face_descriptor(img, shape)

    def compare_faces(self, image_path1: str, image_paths2: List[str]) -> List[float]:
        # 检查资源是否已被释放
        if not hasattr(self, 'detector') or not hasattr(self, 'sp') or not hasattr(self, 'facerec'):
            raise RuntimeError("Resources have been released. Create a new FaceComparator instance.")

        # 加载第一张图片并提取特征
        img1 = io.imread(image_path1)
        faces1 = self.detector(img1, 1)
        face1 = self.get_largest_face(faces1, img1.shape)
        if face1 is None:
            return [0] * len(image_paths2)  # 如果第一张图片没有检测到人脸，返回全0列表
        face_descriptor1 = self.get_face_descriptor(img1, face1)

        similarities = []
        for image_path2 in image_paths2:
            try:
                # 加载第二张图片并提取特征
                img2 = io.imread(image_path2)
                faces2 = self.detector(img2, 1)
                face2 = self.get_largest_face(faces2, img2.shape)

                if face2 is None:
                    similarities.append(0)  # 如果第二张图片没有检测到人脸，相似度为0
                    print(f"未检测到人脸：{image_path2}")
                else:
                    face_descriptor2 = self.get_face_descriptor(img2, face2)
                    # 计算欧氏距离
                    distance = np.linalg.norm(np.array(face_descriptor1) - np.array(face_descriptor2))
                    # 将距离转换为相似度（0到1之间）
                    similarity = 1 / (1 + distance)
                    similarities.append(similarity)
                    print(f"{image_path2} 相似度为：{similarity}")
            except Exception as e:
                print(f"发生错误：{e}")
        return similarities







