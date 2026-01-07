import argparse
import sounddevice as sd


parser = argparse.ArgumentParser(description='语音控制与语音通话整合系统')

devices = sd.query_devices()
device_count = len(devices)

# 默认使用倒数第二个设备（如果设备数量足够）
default_device_id = device_count -1 if device_count >= 2 else 0

# 音频参数
parser.add_argument('--input_device_id', type=int, default=0, help='音频设备ID，-1表示使用默认设备')
parser.add_argument('--output_device_id', type=int, default=0, help='')
parser.add_argument('--input_sample_rate', type=int, default=44100, help='采样率')
parser.add_argument('--output_sample_rate', type=int, default=44100, help='采样率')
parser.add_argument('--input_channels', type=int, default=1, help='')
parser.add_argument('--output_channels', type=int, default=1, help='')
parser.add_argument('--block_size', type=int, default=2048, help='音频块大小')
parser.add_argument('--low_threshold', type=int, default=10, help='低音量阈值')
parser.add_argument('--high_threshold', type=int, default=15, help='高音量阈值')
parser.add_argument('--pre_record', type=int, default=1, help='预录音时长(秒)')
parser.add_argument('--silence_cut', type=int, default=1, help='静音检测时长(秒)')
parser.add_argument('--gain_factor', type=int, default=2, help='增益系数')

# 网络参数in
parser.add_argument('--server_ip', default="shebei1.ztmbec.com", help='语音通话服务器ip')
parser.add_argument('--control_port', default=9000, help='用以接收远程控制端口')
parser.add_argument('--voice_port', default=8088, help='用以进行语音通话的端口')
parser.add_argument('--client_id', type=str, default="passive_client_02", help='客户端ID')
parser.add_argument('--equip_id', type=str, default="1001", help='设备ID')
parser.add_argument('--state_freq', type=int, default=10, help='状态上报频率(秒)')

# 文件路径
parser.add_argument('--save_path', type=str, default="recordings", help='录音保存路径')
parser.add_argument('--voices_path', type=str, default="voices", help='语音文件保存路径')

# TTS参数
parser.add_argument('--model_url', type=str, default="https://api.siliconflow.cn/v1/audio/speech",
                    help='硅基流动的tts网址')
parser.add_argument('--tts_model', type=str, default="FunAudioLLM/CosyVoice2-0.5B")
parser.add_argument('--api_key', type=str, default="sk-dvdwtxdhklaynyozzlrmdqrqfekwyoboidwxfmktswxksoyd",
                    help='TTS API密钥')
parser.add_argument('--voice_id', type=str, default="speech:Go2Warning:abuqmr9rt3:urnvxdnqiejroqksxwym",
                    help='用于硅基流动的音色id')
parser.add_argument('--system_voice', type=str, default="FunAudioLLM/CosyVoice2-0.5B:anna",
                    help='系统预置的音色')
parser.add_argument('--sample_rate', type=int, default=16000)
parser.add_argument('--speed', type=float, default=1.1)

# 解析参数，生成包含所有配置的对象
# 注意：parser 仍然是 ArgumentParser 对象（供 synthesis_client.py 等使用）
# args 是解析后的参数对象，包含所有配置属性（如 args.model_url）
args = parser.parse_args()
