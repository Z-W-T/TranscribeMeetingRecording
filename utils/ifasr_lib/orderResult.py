import json
import re

def parse_order_result(api_response):
    """
    解析完整的API响应，提取orderResult中的所有w字段内容并拼接
    
    参数:
        api_response: 完整的API响应字典
    返回:
        拼接后的文本字符串
    """
    try:
        # 从API响应中获取orderResult字段
        order_result_str = api_response.get('content', {}).get('orderResult', '{}')
        
        # 处理转义字符问题
        cleaned_str = re.sub(r'\\\\', r'\\', order_result_str)
        
        # 解析orderResult字符串为JSON对象
        order_result = json.loads(cleaned_str)
        
        # 提取所有w字段的值
        w_values = []
        
        # 遍历lattice数组
        if 'lattice' in order_result:
            for lattice_item in order_result['lattice']:
                if 'json_1best' in lattice_item:
                    # 解析json_1best字段
                    json_1best = json.loads(lattice_item['json_1best'])
                    
                    # 处理st对象
                    if 'st' in json_1best and 'rt' in json_1best['st']:
                        for rt_item in json_1best['st']['rt']:
                            if 'ws' in rt_item:
                                for ws_item in rt_item['ws']:
                                    if 'cw' in ws_item:
                                        for cw_item in ws_item['cw']:
                                            if 'w' in cw_item:
                                                w_values.append(cw_item['w'])
    
        # 拼接所有w值
        return ''.join(w_values)
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return ""
    except Exception as e:
        print(f"处理过程中出错: {e}")
        return ""

def main():
    # 示例API成功响应（截取部分示例数据）
    sample_api_response = {
        "content": {
            "orderResult": "{\"lattice\":[{\"json_1best\":\"{\\\"st\\\":{\\\"pa\\\":\\\"0\\\",\\\"rt\\\":[{\\\"ws\\\":[{\\\"cw\\\":[{\\\"w\\\":\\\"为\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"0.7511\\\"}],\\\"wb\\\":22,\\\"we\\\":75}]}],\\\"bg\\\":\\\"880\\\",\\\"rl\\\":\\\"1\\\",\\\"ed\\\":\\\"1680\\\"}}\"},{\"json_1best\":\"{\\\"st\\\":{\\\"pa\\\":\\\"0\\\",\\\"rt\\\":[{\\\"ws\\\":[{\\\"cw\\\":[{\\\"w\\\":\\\"喂\\\",\\\"wp\\\":\\\"s\\\",\\\"wc\\\":\\\"0.9806\\\"}],\\\"wb\\\":19,\\\"we\\\":52},{\\\"cw\\\":[{\\\"w\\\":\\\"你好\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"1.0000\\\"}],\\\"wb\\\":53,\\\"we\\\":111},{\\\"cw\\\":[{\\\"w\\\":\\\"｡\\\",\\\"wp\\\":\\\"p\\\",\\\"wc\\\":\\\"0.0000\\\"}],\\\"wb\\\":111,\\\"we\\\":111}]}],\\\"bg\\\":\\\"2390\\\",\\\"rl\\\":\\\"1\\\",\\\"ed\\\":\\\"3640\\\"}}\"},{\"json_1best\":\"{\\\"st\\\":{\\\"pa\\\":\\\"0\\\",\\\"rt\\\":[{\\\"ws\\\":[{\\\"cw\\\":[{\\\"w\\\":\\\"舒\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"0.8630\\\"}],\\\"wb\\\":20,\\\"we\\\":44},{\\\"cw\\\":[{\\\"w\\\":\\\"高\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"1.0000\\\"}],\\\"wb\\\":45,\\\"we\\\":65},{\\\"cw\\\":[{\\\"w\\\":\\\"生\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"0.2461\\\"}],\\\"wb\\\":66,\\\"we\\\":79},{\\\"cw\\\":[{\\\"w\\\":\\\"先生\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"0.9709\\\"}],\\\"wb\\\":80,\\\"we\\\":109},{\\\"cw\\\":[{\\\"w\\\":\\\"是\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"1.0000\\\"}],\\\"wb\\\":110,\\\"we\\\":118},{\\\"cw\\\":[{\\\"w\\\":\\\"吧\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"1.0000\\\"}],\\\"wb\\\":119,\\\"we\\\":138},{\\\"cw\\\":[{\\\"w\\\":\\\"?\\\",\\\"wp\\\":\\\"p\\\",\\\"wc\\\":\\\"0.0000\\\"}],\\\"wb\\\":138,\\\"we\\\":138}]}],\\\"bg\\\":\\\"5130\\\",\\\"rl\\\":\\\"1\\\",\\\"ed\\\":\\\"7200\\\"}}\"}]}",
            "orderInfo": {
                "failType": 0,
                "status": 4,
                "orderId": "DKHJQ202003171520031715109E1FF5E50001D",
                "originalDuration": 14000
            }
        },
        "descInfo": "success",
        "code": "000000"
    }
    
    # 解析并获取拼接后的文本
    result_text = parse_order_result(sample_api_response)
    
    # 展示结果
    print("解析并拼接后的w字段内容：")
    print("----------------------------------------")
    print(result_text)
    print("----------------------------------------")

if __name__ == "__main__":
    main()
    