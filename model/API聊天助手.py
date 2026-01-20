import requests

url = 'http://10.84.9.9:65530/v1/chat-messages'
api_key = 'app-fBXKA9AHjcRjW9rxi7EeJUSn'# 替换为你的实际 API 密钥

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

data = {
    "inputs": {},
    "query": "你是谁",
    "response_mode": "blocking",
    "conversation_id": "",
    "user": "ayang",
    "files": []
}

response = requests.post(url, headers=headers, json=data, verify=False)

#print(response)
print(response.json()['answer'])# 直接读取完整回复
