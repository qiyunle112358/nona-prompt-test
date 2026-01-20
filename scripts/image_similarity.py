"""
图像相似度评估模块
使用多种算法（SSIM、特征匹配、深度学习）并行评估图像相似度
"""

import logging
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, List
from PIL import Image
import cv2

logger = logging.getLogger(__name__)

try:
    from skimage.metrics import structural_similarity as ssim
    SSIM_AVAILABLE = True
except ImportError:
    SSIM_AVAILABLE = False
    logger.warning("scikit-image未安装，SSIM评估将不可用")

# 全局变量，用于标记PyTorch是否可用
TORCH_AVAILABLE = False
try:
    import torch
    import torchvision.transforms as transforms
    from torchvision.models import resnet18
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch未安装，深度学习评估将使用感知哈希替代")

try:
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    logger.warning("imagehash未安装，将使用直方图比较替代")


class ImageSimilarityEvaluator:
    """图像相似度评估器"""
    
    def __init__(self):
        global TORCH_AVAILABLE
        self.device = None
        self.model = None
        self.transform = None
        
        # 初始化深度学习模型（如果可用）
        if TORCH_AVAILABLE:
            try:
                self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                # 使用轻量级的ResNet18作为特征提取器
                self.model = resnet18(pretrained=True)
                self.model.eval()
                self.model = self.model.to(self.device)
                # 移除最后的分类层，只保留特征提取部分
                self.model = torch.nn.Sequential(*list(self.model.children())[:-1])
                
                self.transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                       std=[0.229, 0.224, 0.225])
                ])
                logger.info("深度学习模型已加载（ResNet18）")
            except Exception as e:
                logger.warning(f"深度学习模型加载失败: {e}，将使用感知哈希替代")
                TORCH_AVAILABLE = False
    
    def load_image(self, image_path: Path) -> np.ndarray:
        """加载图像为numpy数组"""
        try:
            img = Image.open(image_path).convert('RGB')
            return np.array(img)
        except Exception as e:
            logger.error(f"加载图像失败 {image_path}: {e}")
            return None
    
    def calculate_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """计算SSIM相似度"""
        if not SSIM_AVAILABLE:
            return 0.0
        
        try:
            # 转换为灰度图
            if len(img1.shape) == 3:
                gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
            else:
                gray1 = img1
            
            if len(img2.shape) == 3:
                gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
            else:
                gray2 = img2
            
            # 调整尺寸使其相同
            h1, w1 = gray1.shape
            h2, w2 = gray2.shape
            if h1 != h2 or w1 != w2:
                gray2 = cv2.resize(gray2, (w1, h1))
            
            # 计算SSIM
            score = ssim(gray1, gray2, data_range=255)
            return float(score)
        except Exception as e:
            logger.error(f"SSIM计算失败: {e}")
            return 0.0
    
    def calculate_feature_match(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """使用ORB特征匹配计算相似度"""
        try:
            # 转换为灰度图
            if len(img1.shape) == 3:
                gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
            else:
                gray1 = img1
            
            if len(img2.shape) == 3:
                gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
            else:
                gray2 = img2
            
            # 调整尺寸
            h1, w1 = gray1.shape
            h2, w2 = gray2.shape
            if h1 != h2 or w1 != w2:
                gray2 = cv2.resize(gray2, (w1, h1))
            
            # 创建ORB检测器
            orb = cv2.ORB_create(nfeatures=500)
            
            # 检测关键点和描述符
            kp1, des1 = orb.detectAndCompute(gray1, None)
            kp2, des2 = orb.detectAndCompute(gray2, None)
            
            if des1 is None or des2 is None or len(des1) == 0 or len(des2) == 0:
                return 0.0
            
            # 使用BFMatcher进行匹配
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            matches = bf.knnMatch(des1, des2, k=2)
            
            # 应用Lowe's ratio test
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.75 * n.distance:
                        good_matches.append(m)
            
            # 计算匹配率
            match_ratio = len(good_matches) / max(len(kp1), len(kp2), 1)
            # 归一化到0-1范围
            score = min(match_ratio * 2.0, 1.0)  # 假设50%匹配率对应1.0分
            return float(score)
        except Exception as e:
            logger.error(f"特征匹配计算失败: {e}")
            return 0.0
    
    def calculate_deep_learning(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """使用深度学习模型计算相似度"""
        global TORCH_AVAILABLE
        if not TORCH_AVAILABLE or self.model is None:
            # 降级到感知哈希
            return self.calculate_perceptual_hash(img1, img2)
        
        try:
            # 预处理图像
            pil_img1 = Image.fromarray(img1)
            pil_img2 = Image.fromarray(img2)
            
            img1_tensor = self.transform(pil_img1).unsqueeze(0).to(self.device)
            img2_tensor = self.transform(pil_img2).unsqueeze(0).to(self.device)
            
            # 提取特征
            with torch.no_grad():
                feat1 = self.model(img1_tensor).squeeze().cpu().numpy()
                feat2 = self.model(img2_tensor).squeeze().cpu().numpy()
            
            # 计算余弦相似度
            feat1_norm = feat1 / (np.linalg.norm(feat1) + 1e-8)
            feat2_norm = feat2 / (np.linalg.norm(feat2) + 1e-8)
            similarity = np.dot(feat1_norm, feat2_norm)
            
            # 归一化到0-1范围（余弦相似度范围是-1到1）
            score = (similarity + 1) / 2.0
            return float(score)
        except Exception as e:
            logger.warning(f"深度学习评估失败: {e}，使用感知哈希替代")
            return self.calculate_perceptual_hash(img1, img2)
    
    def calculate_perceptual_hash(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """使用感知哈希计算相似度（轻量级替代方案）"""
        if not IMAGEHASH_AVAILABLE:
            return self.calculate_histogram_similarity(img1, img2)
        
        try:
            # 转换为PIL Image
            pil_img1 = Image.fromarray(img1)
            pil_img2 = Image.fromarray(img2)
            
            # 计算感知哈希
            hash1 = imagehash.phash(pil_img1)
            hash2 = imagehash.phash(pil_img2)
            
            # 计算汉明距离
            hamming_distance = hash1 - hash2
            # 转换为相似度分数（0-1）
            max_distance = 64  # 感知哈希的最大距离
            similarity = 1.0 - (hamming_distance / max_distance)
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            logger.error(f"感知哈希计算失败: {e}")
            return self.calculate_histogram_similarity(img1, img2)
    
    def calculate_histogram_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """使用直方图比较计算相似度（最基础的替代方案）"""
        try:
            # 调整尺寸
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]
            if h1 != h2 or w1 != w2:
                img2 = cv2.resize(img2, (w1, h1))
            
            # 计算直方图
            hist1 = cv2.calcHist([img1], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
            hist2 = cv2.calcHist([img2], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
            
            # 计算相关性
            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            return float(correlation)
        except Exception as e:
            logger.error(f"直方图比较失败: {e}")
            return 0.0
    
    def evaluate_similarity(self, original_path: Path, generated_path: Path) -> Dict[str, float]:
        """
        评估两张图像的相似度
        
        Returns:
            包含各种算法得分的字典
        """
        img1 = self.load_image(original_path)
        img2 = self.load_image(generated_path)
        
        if img1 is None or img2 is None:
            return {
                'ssim': 0.0,
                'feature_match': 0.0,
                'deep_learning': 0.0,
                'weighted_score': 0.0
            }
        
        # 并行计算各种相似度
        ssim_score = self.calculate_ssim(img1, img2)
        feature_score = self.calculate_feature_match(img1, img2)
        dl_score = self.calculate_deep_learning(img1, img2)
        
        # 加权平均（权重可根据效果调整）
        weights = {
            'ssim': 0.4,          # SSIM权重最高，因为它对结构相似度最敏感
            'feature_match': 0.3,  # 特征匹配权重中等
            'deep_learning': 0.3   # 深度学习权重中等
        }
        
        weighted_score = (
            weights['ssim'] * ssim_score +
            weights['feature_match'] * feature_score +
            weights['deep_learning'] * dl_score
        )
        
        return {
            'ssim': ssim_score,
            'feature_match': feature_score,
            'deep_learning': dl_score,
            'weighted_score': weighted_score
        }
