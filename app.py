from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from main import AI2SQLService
import test_runner
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

# 初始化服务
service = AI2SQLService()

# 存储查询日志（使用字典，key为查询ID）
query_logs = {}


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
        result = service.query_with_retries(question, verbose=False, collect_logs=True)
        
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
        return jsonify({
            "success": result["success"],
            "question": result["question"],
            "sql": result["sql"],
            "rows": result["rows"],
            "summary": result["summary"],
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

