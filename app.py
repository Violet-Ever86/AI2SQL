from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from main import AI2SQLService
import test_runner
from datetime import datetime
import uuid
import os
import tempfile
from config.config import logger

app = Flask(__name__)
CORS(app)

# 初始化服务
service = AI2SQLService()

# 存储查询日志（使用字典，key为查询ID）
query_logs = {}

# 尝试初始化语音识别服务（可选）
speech_service = None
try:
    # 如果配置了模型路径，可以在这里初始化
    # 注意：需要根据实际环境修改模型路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_model_dir = os.path.join(base_dir, "model", "SenseVoiceSmall")
    default_vad_model = os.path.join(base_dir, "model", "speech_fsmn_vad_zh-cn-16k-common-pytorch")

    model_dir = os.getenv('FUNASR_MODEL_DIR', default_model_dir if os.path.exists(default_model_dir) else None)
    vad_model = os.getenv('FUNASR_VAD_MODEL', default_vad_model if os.path.exists(default_vad_model) else None)
    # 设备选择：环境变量优先；若未指定，则根据 torch 能力自动选择
    env_device = os.getenv('FUNASR_DEVICE')
    if env_device:
        device = env_device
    else:
        try:
            import torch  # noqa: WPS433

            device = "cuda:0" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"

    if model_dir and vad_model:
        from voice.stt_service import get_stt_service
        speech_service = get_stt_service(model_dir, vad_model, device=device)
        if speech_service.is_available():
            logger.info(f"语音识别服务已初始化，模型: {model_dir}, VAD: {vad_model}, 设备: {device}")
        else:
            logger.warning("语音识别服务初始化失败，请检查模型路径或依赖")
    else:
        logger.info("未配置 FunASR 模型路径，将使用浏览器原生语音识别")
except Exception as e:
    logger.error(f"语音识别服务初始化失败: {e}")
    speech_service = None


@app.route('/')
def index():
    """前端页面"""
    return render_template('index.html')


@app.route('/test')
def test():
    """测试页面"""
    return render_template('test.html')


@app.route('/api/test-questions', methods=['GET'])
def get_test_questions():
    """获取测试问题列表API"""
    try:
        questions = []
        for test_id, question in test_runner.TEST_QUESTIONS:
            # 从test_id中提取category（如"基础-1" -> "基础"）
            category = test_id.split('-')[0] if '-' in test_id else '其他'
            questions.append({
                "id": test_id,
                "category": category,
                "question": question
            })
        
        return jsonify({
            "success": True,
            "questions": questions
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取测试问题失败: {str(e)}"
        }), 500


@app.route('/api/query', methods=['POST'])
def query():
    """查询API接口"""
    try:
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                "success": False,
                "error": "问题不能为空"
            }), 400
        
        # 生成查询ID
        query_id = str(uuid.uuid4())
        
        # 调用服务查询（收集日志，带整体重试机制）
        # 当本次查询出现错误（包括SQL未通过校验等）时，会自动重新调用大模型，最多尝试3次
        result = service.query_with_retries(question, collect_logs=True)
        
        # 存储日志
        query_logs[query_id] = {
            "question": question,
            "timestamp": datetime.now().isoformat(),
            "logs": result.get("logs", []),
            "template_info": result.get("template_info"),
            "sql": result.get("sql"),
            "success": result.get("success"),
            "error": result.get("error"),
            "attempts": result.get("attempts", 1),
        }
        
        # 返回结果（包含查询ID用于后续查看日志）
        # summary现在是字典格式：{"summaryContent": "...", "keyInfo": "...", "recordOverview": "..."}
        return jsonify({
            "success": result["success"],
            "question": result["question"],
            "sql": result["sql"],
            "rows": result["rows"],
            "summary": result.get("summary", {}),  # 结构化summary字典
            "error": result.get("error"),
            "query_id": query_id,
            "template_info": result.get("template_info"),
            "attempts": result.get("attempts", 1),
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"服务器错误: {str(e)}"
        }), 500


@app.route('/api/query-logs/<query_id>', methods=['GET'])
def get_query_logs(query_id):
    """获取查询日志API"""
    try:
        if query_id in query_logs:
            return jsonify({
                "success": True,
                "logs": query_logs[query_id]
            })
        else:
            return jsonify({
                "success": False,
                "error": "日志不存在"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取日志失败: {str(e)}"
        }), 500


@app.route('/api/receive_roles', methods=['POST'])
def get_login_roles(quest: dict):

    pass


@app.route('/api/speech-recognize', methods=['POST'])
def speech_recognize():
    """语音识别API接口（使用后端FunASR模型）"""
    if not speech_service or not speech_service.is_available():
        return jsonify({
            "success": False,
            "error": "后端语音识别服务不可用，请使用浏览器原生语音识别"
        }), 503
    
    try:
        # 检查是否有文件上传
        if 'audio' not in request.files:
            return jsonify({
                "success": False,
                "error": "未找到音频文件"
            }), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({
                "success": False,
                "error": "音频文件为空"
            }), 400
        
        # 保存临时文件，接受 wav/webm 等，非 wav 尝试转成 16k 单声道 wav
        original_suffix = (os.path.splitext(audio_file.filename)[1] or '.wav').lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=original_suffix) as tmp_file:
            audio_file.save(tmp_file.name)
            tmp_path = tmp_file.name

        converted_path = None
        # 如果不是 wav，使用 ffmpeg 转码为 16k 单声道 wav
        if original_suffix != '.wav':
            try:
                import subprocess

                fd, converted_path = tempfile.mkstemp(suffix='.wav')
                os.close(fd)

                # 使用 ffmpeg 转码，要求系统 PATH 中已经配置好 ffmpeg
                # -ar 16000: 采样率 16k
                # -ac 1: 单声道
                cmd = [
                    "ffmpeg",
                    "-y",              # 覆盖输出文件
                    "-i", tmp_path,    # 输入文件
                    "-ar", "16000",    # 目标采样率
                    "-ac", "1",        # 单声道
                    converted_path,
                ]
                subprocess.run(
                    cmd,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                use_path = converted_path
            except Exception as conv_err:
                logger.warning(f"音频转码失败，将直接使用原文件: {conv_err}")
                use_path = tmp_path
        else:
            use_path = tmp_path
        
        try:
            # 进行语音识别
            text = speech_service.recognize(use_path)
            
            if text:
                return jsonify({
                    "success": True,
                    "text": text
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "未能识别出语音内容"
                }), 400
        finally:
            # 清理临时文件
            for p in [tmp_path, converted_path] if 'converted_path' in locals() else [tmp_path]:
                if p:
                    try:
                        os.unlink(p)
                    except Exception:
                        pass
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"语音识别失败: {str(e)}"
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

