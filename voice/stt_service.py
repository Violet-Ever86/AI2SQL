"""
轻量化语音识别服务（仅 STT，不含机器人控制逻辑）
依赖：funasr
"""

import os
import logging
from typing import Optional
from config.config import logger

# 禁用funasr的cli_utils日志
logging.getLogger("funasr.utils.cli_utils").disabled = True

try:
    from funasr.utils.postprocess_utils import rich_transcription_postprocess
    from funasr import AutoModel
    FUNASR_AVAILABLE = True
except ImportError:
    FUNASR_AVAILABLE = False
    print("警告：未安装 funasr，STT 服务不可用")


class STTService:
    """基于 FunASR 的语音转文本服务"""

    def __init__(self, model_dir: str, vad_model: str, device: str = "cuda:0"):
        """
        Args:
            model_dir: 识别模型路径（如 SenseVoiceSmall）
            vad_model: VAD 模型路径（如 fsmn_vad）
            device:    计算设备，"cuda:0" 或 "cpu"
        """
        self.model_dir = model_dir
        self.vad_model = vad_model
        self.device = device
        self.model = None
        self.initialized = False

        if FUNASR_AVAILABLE:
            self._init_model()
        else:
            print("FunASR 不可用，跳过模型初始化")

    def _init_model(self):
        if not os.path.exists(self.model_dir):
            print(f"STT 模型路径不存在: {self.model_dir}")
            return
        if not os.path.exists(self.vad_model):
            print(f"VAD 模型路径不存在: {self.vad_model}")
            return

        print("正在初始化 FunASR 语音识别模型...")
        try:
            self.model = AutoModel(
                model=self.model_dir,
                vad_model=self.vad_model,
                vad_kwargs={"max_single_segment_time": 30000},
                device=self.device,
                disable_download=True,
                disable_update=True,
                disable_log=True,
                disable_pbar=True,
                log_level="ERROR",
            )
            self.initialized = True
            print("FunASR 语音识别模型初始化完成")
        except Exception as e:
            print(f"FunASR 模型初始化失败: {e}")
            self.initialized = False

    def is_available(self) -> bool:
        """服务是否可用"""
        return FUNASR_AVAILABLE and self.initialized and self.model is not None

    def recognize(self, audio_path: str) -> str:
        """
        对音频文件进行语音识别
        推荐输入：16k 单声道 wav
        返回：识别文本（失败返回空字符串）
        """
        if not self.is_available():
            return ""
        if not os.path.exists(audio_path):
            print(f"音频文件不存在: {audio_path}")
            return ""

        try:
            result = self.model.generate(
                input=audio_path,
                cache={},
                language="zn",
                use_itn=True,
                batch_size_s=60,
                merge_vad=True,
                merge_length_s=15,
                disable_log=True,
            )
            if not result or "text" not in result[0]:
                return ""
            text = rich_transcription_postprocess(result[0]["text"])
            return text.strip()
        except Exception as e:
            print(f"语音识别失败: {e}")
            return ""


# 可选的全局单例获取
_stt_service: Optional[STTService] = None


def get_stt_service(model_dir: str, vad_model: str, device: str = "cuda:0") -> STTService:
    """获取 STTService 单例"""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService(model_dir, vad_model, device=device)
    return _stt_service

