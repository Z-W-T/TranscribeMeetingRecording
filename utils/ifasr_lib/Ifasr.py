# -*- coding: utf-8 -*-
import base64
import hmac
import json
import os
import time
import random
import string
import requests
import urllib.parse
import datetime
import warnings
import wave  # 使用Python内置的wave模块，无需额外安装
from . import orderResult

# 忽略SSL验证警告（生产环境建议开启验证）
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

# 讯飞API基础配置
LFASR_HOST = "https://office-api-ist-dx.iflyaisol.com"
API_UPLOAD = "/v2/upload"
API_GET_RESULT = "/v2/getResult"


class XfyunAsrClient:
    def __init__(self, appid, access_key_id, access_key_secret, audio_file_path):
        self.appid = appid
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.audio_file_path = self._check_audio_path(audio_file_path)
        self.audio_duration = self._get_wav_duration_ms()  # 获取音频时长（毫秒，整数）
        self.order_id = None
        self.signature_random = self._generate_random_str()
        self.last_base_string = ""  # 签名原始串（编码后）
        self.last_signature = ""    # 最终签名
        self.upload_url = ""        # 最终生成的请求URL

    def _check_audio_path(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"音频文件不存在：{path}")
        # 校验是否为WAV文件
        if not path.lower().endswith(".wav"):
            raise ValueError(f"当前代码仅支持WAV格式音频，您的文件格式为：{os.path.splitext(path)[1]}")
        return os.path.abspath(path)

    def _generate_random_str(self, length=16):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _get_local_time_with_tz(self):
        """生成带时区偏移的本地时间（格式：yyyy-MM-dd'T'HH:mm:ss±HHmm）"""
        local_now = datetime.datetime.now()
        tz_offset = local_now.astimezone().strftime('%z')  # 输出格式：+0800 或 -0500
        return f"{local_now.strftime('%Y-%m-%dT%H:%M:%S')}{tz_offset}"

    def _get_wav_duration_ms(self):
        """
        用Python内置wave模块获取WAV音频时长（毫秒，整数）
        原理：时长(毫秒) = 总帧数 / 采样率 * 1000
        """
        try:
            with wave.open(self.audio_file_path, 'rb') as wav_file:
                # 获取WAV文件关键参数：nframes=总帧数，framerate=采样率（Hz）
                n_frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                
                # 计算时长（毫秒），转换为整数
                duration_ms = int(round(n_frames / sample_rate * 1000))
                return duration_ms
        except wave.Error as e:
            raise Exception(f"WAV文件解析失败：{str(e)}，请确认文件为标准WAV格式（非损坏、非压缩）")
        except Exception as e:
            raise Exception(f"获取音频时长失败：{str(e)}")

    def generate_signature(self, params):
        """生成签名（根据文档要求：对key和value都进行url encode后生成baseString）"""
        # 排除signature参数，按参数名自然排序（与Java TreeMap一致）
        sign_params = {k: v for k, v in params.items() if k != "signature"}
        sorted_params = sorted(sign_params.items(), key=lambda x: x[0])
        
        # 构建baseString：对key和value都进行URL编码
        base_parts = []
        for k, v in sorted_params:
            if v is not None and str(v).strip() != "":
                encoded_key = urllib.parse.quote(k, safe='')  # 参数名编码
                encoded_value = urllib.parse.quote(str(v), safe='')  # 参数值编码
                base_parts.append(f"{encoded_key}={encoded_value}")
        
        self.last_base_string = "&".join(base_parts)
        
        # HMAC-SHA1加密 + Base64编码
        hmac_obj = hmac.new(
            self.access_key_secret.encode("utf-8"),
            self.last_base_string.encode("utf-8"),
            digestmod="sha1"
        )
        self.last_signature = base64.b64encode(hmac_obj.digest()).decode("utf-8")
        return self.last_signature

    def upload_audio(self):
        # 1. 基础参数准备（duration字段为毫秒整数）
        audio_size = str(os.path.getsize(self.audio_file_path))  # 音频文件大小（字节）
        audio_name = os.path.basename(self.audio_file_path)      # 音频文件名
        date_time = self._get_local_time_with_tz()               # 带时区的本地时间
        print(f"音频文件：{audio_name}\n文件大小：{audio_size} 字节\n音频时长：{self.audio_duration} 毫秒")  # 打印信息

        # 2. 构建URL参数 - duration字段为毫秒整数
        url_params = {
            "appId": self.appid,
            "accessKeyId": self.access_key_id,
            "dateTime": date_time,
            "signatureRandom": self.signature_random,
            "fileSize": audio_size,
            "fileName": audio_name,
            "language": "autodialect",
            "roleType": 1,
            "duration": str(self.audio_duration)  # 音频时长（毫秒，整数字符串）
        }

        # 3. 生成签名（duration参数参与签名计算）
        signature = self.generate_signature(url_params)
        if not signature:
            raise Exception("签名生成失败，结果为空")

        # 4. 构建请求头
        headers = {
            "Content-Type": "application/octet-stream",
            "signature": signature
        }

        # 5. 构建最终请求URL
        encoded_params = []
        for k, v in url_params.items():
            encoded_key = urllib.parse.quote(k, safe='')
            encoded_v = urllib.parse.quote(str(v), safe='')
            encoded_params.append(f"{encoded_key}={encoded_v}")
        self.upload_url = f"{LFASR_HOST}{API_UPLOAD}?{'&'.join(encoded_params)}"

        # 6. 读取音频文件并发送POST请求
        with open(self.audio_file_path, "rb") as f:
            audio_data = f.read()

        try:
            response = requests.post(
                url=self.upload_url,
                headers=headers,
                data=audio_data,
                timeout=30,
                verify=False  # 测试环境关闭SSL验证
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"上传请求网络失败：{str(e)}")

        # 7. 解析响应结果
        try:
            result = json.loads(response.text)
            print("上传结果：",result)
        except json.JSONDecodeError:
            raise Exception(f"API返回非JSON数据：{response.text}")

        # 8. 处理API业务错误
        if result.get("code") != "000000":
            raise Exception(
                f"上传失败（API错误）：\n"
                f"错误码：{result.get('code')}\n"
                f"错误描述：{result.get('descInfo', '未知错误')}\n"
                f"请求URL：{self.upload_url}\n"
                f"签名原始串：{self.last_base_string}\n"
                f"签名值：{self.last_signature}"
            )

        # 9. 上传成功，记录订单ID
        self.order_id = result["content"]["orderId"]
        print(f"上传成功！订单ID：{self.order_id}")
        return result

    def get_transcribe_result(self):
        """查询音频转写结果（轮询直到完成/超时）"""
        if not self.order_id:
            print("\n未检测到订单ID，自动执行上传流程...")
            self.upload_audio()
        if not self.order_id:
            raise Exception("未获取到订单ID，无法查询转写结果")

        # 构建查询参数
        query_params = {
            "appId": self.appid,
            "accessKeyId": self.access_key_id,
            "dateTime": self._get_local_time_with_tz(),
            "ts": str(int(time.time())),  # 秒级时间戳
            "orderId": self.order_id,
            "signatureRandom": self.signature_random
        }

        # 生成查询签名
        query_signature = self.generate_signature(query_params)
        query_headers = {
            "Content-Type": "application/json",
            "signature": query_signature
        }

        # 构建查询URL
        encoded_query_params = []
        for k, v in query_params.items():
            encoded_key = urllib.parse.quote(k, safe='')
            encoded_v = urllib.parse.quote(str(v), safe='')
            encoded_query_params.append(f"{encoded_key}={encoded_v}")
        query_url = f"{LFASR_HOST}{API_GET_RESULT}?{'&'.join(encoded_query_params)}"

        # 轮询查询
        max_retry = 10000
        retry_count = 0
        while retry_count < max_retry:
            try:
                response = requests.post(
                    url=query_url,
                    headers=query_headers,
                    data=json.dumps({}),
                    timeout=15,
                    verify=False
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise Exception(f"查询请求网络失败：{str(e)}")

            try:
                result = json.loads(response.text)
                # print(result)
            except json.JSONDecodeError:
                raise Exception(f"查询响应非JSON数据：{response.text}")

            if result.get("code") != "000000":
                raise Exception(f"查询失败（API错误）：{result.get('descInfo', '未知错误')}")

            # 转写状态：3=处理中，4=完成
            process_status = result["content"]["orderInfo"]["status"]
            if process_status == 4:
                print("转写完成！")
                return result
            elif process_status != 3:
                raise Exception(f"转写异常：状态码={process_status}，描述={result.get('descInfo')}")

            # 处理中，等待5秒后重试
            retry_count += 1
            print(f"转写处理中（已查询{retry_count}/{max_retry}次），10秒后再次查询...")
            time.sleep(10)

        raise Exception(f"查询超时：已重试{max_retry}次，订单ID：{self.order_id}")

if __name__ == "__main__":
    # -------------------------- 请替换为你的真实参数 --------------------------
    XFYUN_APPID = "91a95634"  # 你的讯飞appId
    XFYUN_ACCESS_KEY_ID = "fd334d091ebb1f535c1a6b5021e4cba3"  # 你的accessKeyId
    XFYUN_ACCESS_KEY_SECRET = "ZmQ2YjhlNTZhYjQ4OGEyNGEyYTg2ZjE2"  # 你的accessKeySecret
    AUDIO_FILE = r"C:\Users\12049\Desktop\TranscribeMeetingRecording\data\dialogue_recording.wav"  # WAV音频文件路径
    # --------------------------------------------------------------------------

    try:
        # 初始化客户端并执行完整转写流程
        asr_client = XfyunAsrClient(
            appid=XFYUN_APPID,
            access_key_id=XFYUN_ACCESS_KEY_ID,
            access_key_secret=XFYUN_ACCESS_KEY_SECRET,
            audio_file_path=AUDIO_FILE
        )
        final_result = asr_client.get_transcribe_result()

        result = orderResult.parse_order_result(final_result)

        # 提取并打印最终转写文本
        
        print("\n" + "="*50)
        print("=== 最终音频转写结果 ===")
        print(f"转写文本：\n{result}")
        print("="*50)

    except Exception as e:
        print("\n" + "="*50)
        print("=== 程序执行失败 ===")
        print(f"错误原因：{str(e)}")
        print("="*50)
