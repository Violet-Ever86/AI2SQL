from config.param_normalizer import ParamNormalizer
from sql.sql_templates import SQLTemplateManager
from sql.sql_validator import SQLValidator
from sql.sql_generator import SQLGenerator
from model.summarizer import Summarizer
from model.llm_client import LLMClient
from data.database import Database
from config.config import params
from typing import Dict
import json
import sys
import re
import os


class AI2SQLService:
    def __init__(self):
        """初始化服务，加载配置和组件"""
        # 加载schema文本
        if os.path.exists(params.schema_path):
            with open(params.schema_path, "r", encoding="utf-8") as f:
                self.schema = f.read().strip()
        else:
            self.schema = ''

        # 构建数据库配置字典
        db_config = {
            "host": params.db_host,
            "port": params.db_port,
            "user": params.db_user,
            "password": params.db_password,
            "db": params.db_name,
        }

        # 初始化各个组件
        self.llm_client = LLMClient(
            endpoint=params.llm_endpoint,
            model=params.llm_model,
            api_key=params.llm_api_key,
            api_type=params.llm_api_type,
        )

        self.param_normalizer = ParamNormalizer()
        self.sql_generator = SQLGenerator(self.param_normalizer)
        self.sql_validator = SQLValidator()
        self.database = Database(db_config)
        self.summarizer = Summarizer(self.llm_client)
        self.template_manager = SQLTemplateManager()

        # 提取允许的表名（用于SQL验证）
        self.allowed_tables = []
        if self.schema:
            tbls = re.findall(r"表名[:：]\s*([\\w`]+)", self.schema, flags=re.I)
            self.allowed_tables = [t.replace("`", "") for t in tbls]

        if not self.schema:
            print("警告：schema_prompt.txt 为空，请先填入三张表的结构。")

    def query(self, question: str, verbose: bool = True) -> Dict:
        """
        处理单个查询问题
        
        Args:
            question: 自然语言问题
            verbose: 是否打印详细信息（默认True）
        
        Returns:
            包含查询结果的字典：
            {
                "question": str,           # 用户问题
                "sql": str,                 # 生成的SQL
                "rows": List[Dict],         # 查询结果
                "summary": str,             # 总结
                "template_info": Dict,      # 模板信息（可选）
                "error": Optional[str],     # 错误信息（如果有）
                "success": bool              # 是否成功
            }
        """
        result = {
            "question": question,
            "sql": "",
            "rows": [],
            "summary": "",
            "template_info": None,
            "error": None,
            "success": False,
        }

        try:
            # 生成SQL提示词
            prompt = self.sql_generator.build_sql_prompt(question, self.schema)
            llm_output = self.llm_client.complete(prompt)

            if verbose:
                print(f"\n--- 模型输出（模板选择） ---\n{llm_output}")

            # 尝试提取模板信息用于显示
            try:
                template_id, params_dict = self.sql_generator.extract_template_and_params(llm_output)
                template = self.template_manager.get_template(template_id)
                result["template_info"] = {
                    "template_id": template_id,
                    "description": template['desc'],
                    "params": params_dict,
                }
                if verbose:
                    print(f"\n--- 选择的模板 ---\n模板ID: {template_id}\n描述: {template['desc']}\n参数: {json.dumps(params_dict, ensure_ascii=False)}")
                    print(f"\n--- 调试：参数详情 ---")
                    for key, value in params_dict.items():
                        print(f"  {key}: {repr(value)} (type: {type(value).__name__})")
            except Exception as e:
                if verbose:
                    print(f"\n--- 模型输出解析错误 ---\n错误: {e}\n原始输出: {llm_output}")

            # 生成SQL
            sql = self.sql_generator.extract_sql(llm_output)
            result["sql"] = sql

            if verbose:
                print(f"\n--- 生成的SQL ---\n{sql}")

            # 验证SQL
            if not self.sql_validator.validate_sql(sql, self.allowed_tables):
                error_msg = "生成的 SQL 未通过校验"
                result["error"] = error_msg
                if verbose:
                    print(f"\n错误：{error_msg}\nSQL: {sql}")
                return result

            # 执行查询
            if verbose:
                print("\n--- 执行 SQL ---\n", sql)

            rows = self.database.run_query(sql)
            result["rows"] = rows

            if verbose:
                print(f"\n--- 查询结果（前5行，实际{len(rows)}行） ---")
                print(json.dumps(rows[:5], ensure_ascii=False, indent=2))

            # 生成总结
            summary = self.summarizer.summarize(question, sql, rows)
            result["summary"] = summary
            result["success"] = True

            if verbose:
                print("\n--- 总结 ---\n", summary)

        except Exception as e:
            error_msg = f"查询处理失败: {str(e)}"
            result["error"] = error_msg
            if verbose:
                print(f"\n错误：{error_msg}")
                import traceback
                traceback.print_exc()

        return result

    def run_interactive(self):
        """运行交互式循环，持续问询直到用户退出"""
        print("=" * 60)
        print("AI转SQL服务已启动")
        print("输入问题开始查询，输入 'quit' 或 'exit' 退出")
        print("=" * 60)

        # 标记是否已使用命令行参数中的问题
        used_cmdline_question = False

        while True:
            try:
                # 如果命令行参数中有问题且还未使用，先使用它
                if params.question and not used_cmdline_question:
                    question = params.question
                    used_cmdline_question = True
                else:
                    question = input("\n请输入你的问题：").strip()

                # 检查退出命令
                if not question or question.lower() in ['quit', 'exit', 'q', '退出']:
                    print("\n感谢使用，再见！")
                    break

                # 处理查询
                result = self.query(question, verbose=True)

                # 如果失败，显示错误信息
                if not result["success"]:
                    print(f"\n❌ 查询失败: {result.get('error', '未知错误')}")

            except KeyboardInterrupt:
                print("\n\n检测到中断信号，退出程序...")
                break
            except EOFError:
                print("\n\n检测到输入结束，退出程序...")
                break
            except Exception as e:
                print(f"\n❌ 发生未预期的错误: {e}")
                import traceback
                traceback.print_exc()


def main():
    """主函数入口"""
    service = AI2SQLService()
    
    # 如果命令行提供了问题，直接查询一次后退出
    if params.question:
        result = service.query(params.question, verbose=True)
        if not result["success"]:
            sys.exit(1)
    else:
        # 否则进入交互式循环
        service.run_interactive()


if __name__ == "__main__":
    main()
