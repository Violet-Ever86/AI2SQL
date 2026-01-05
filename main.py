from config.param_normalizer import ParamNormalizer
from sql.sql_templates import SQLTemplateManager
from sql.sql_validator import SQLValidator
from sql.sql_generator import SQLGenerator
from sql.sql_field_replacer import SQLFieldReplacer
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
        self.sql_field_replacer = SQLFieldReplacer()
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

    def query(self, question: str, verbose: bool = True, collect_logs: bool = False) -> Dict:
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
            "logs": [] if collect_logs else None,
        }
        
        # 日志收集函数
        def log(message):
            if collect_logs:
                result["logs"].append(message)
            if verbose:
                print(message)

        try:
            # 生成SQL提示词
            prompt = self.sql_generator.build_sql_prompt(question, self.schema)
            # 增加 max_tokens 以确保输出完整（JSON响应通常需要更多token）
            # 注意：这里的 max_tokens 只是客户端请求上限，服务端如果还有更小的限制，仍需在LLM服务配置中调整
            llm_output = self.llm_client.complete(prompt, max_tokens=10000)
            
            # 检查输出是否完整
            if not llm_output or len(llm_output.strip()) < 10:
                error_msg = "模型输出为空或过短，请检查LLM服务是否正常"
                result["error"] = error_msg
                log(f"\n错误：{error_msg}")
                return result
            
            # 检查JSON是否完整（简单检查：是否包含闭合的花括号）
            stripped_output = llm_output.strip()
            if stripped_output.startswith('{') and not stripped_output.rstrip().endswith('}'):
                # 输出可能被截断
                error_msg = f"模型输出不完整（未以}}结尾），可能被截断。输出内容: {stripped_output[:200]}..."
                result["error"] = error_msg + "\n建议：1. 检查LLM服务的max_tokens配置\n2. 尝试简化问题\n3. 联系管理员检查模型配置"
                log(f"\n警告：{error_msg}")
                return result

            # 尝试提取模板信息用于显示（包括模板匹配度）
            try:
                template_id, params_dict, _free_sql, template_score = self.sql_generator.extract_template_and_params(llm_output)

                # 只有在不是自由模式时才从模板管理器中取描述
                if template_id and template_id.lower() != "free":
                    template = self.template_manager.get_template(template_id)
                    result["template_info"] = {
                        "template_id": template_id,
                        "description": template['desc'],
                        "params": params_dict,
                        "score": template_score,
                    }

                    # 始终输出到终端
                    log(f"\n--- 选择的模板 ---")
                    log(f"模板ID: {template_id}")
                    log(f"描述: {template['desc']}")
                    log(f"匹配度(score): {template_score:.3f}")
                    log(f"参数: {json.dumps(params_dict, ensure_ascii=False)}")
                    log(f"\n--- 调试：参数详情 ---")
                    for key, value in params_dict.items():
                        log(f"  {key}: {repr(value)} (type: {type(value).__name__})")
                else:
                    # 自由模式，仅输出解析结果
                    result["template_info"] = {
                        "template_id": "free",
                        "description": "自由生成SQL（未使用预定义模板）",
                        "params": params_dict,
                        "score": template_score,
                    }
                    log(f"\n--- 自由模式（未使用模板） ---")
                    log(f"匹配度(score): {template_score:.3f}")
                    log(f"解析到的参数: {json.dumps(params_dict, ensure_ascii=False)}")

            except Exception as e:
                log(f"\n--- 模型输出解析错误 ---\n错误: {e}\n原始输出: {llm_output}")
                # 如果是输出不完整的错误，提供更友好的提示
                if "不完整" in str(e) or "截断" in str(e) or len(llm_output.strip()) < 50:
                    result["error"] = f"模型输出不完整或格式错误。\n错误: {str(e)}\n输出内容: {llm_output[:200]}...\n\n建议：\n1. 检查LLM服务配置和max_tokens设置\n2. 尝试简化问题\n3. 联系管理员检查模型配置"
                    return result
                # 如果是输出不完整的错误，提供更友好的提示
                if "不完整" in str(e) or "截断" in str(e):
                    result["error"] = f"模型输出不完整，可能是max_tokens设置过小。建议：\n1. 检查LLM服务配置\n2. 尝试简化问题\n3. 联系管理员检查模型配置\n\n错误详情: {str(e)}"
                    return result

            # 基于LLM输出生成并校验SQL，如校验失败则重新调用LLM最多六次重新生成SQL
            max_sql_gen_retries = 6
            sql = ""
            for gen_attempt in range(1, max_sql_gen_retries + 1):
                if gen_attempt > 1:
                    log(f"\n提示：第 {gen_attempt} 次尝试重新生成 SQL（上一次未通过校验）")
                    # 重新调用LLM生成输出
                    llm_output = self.llm_client.complete(prompt, max_tokens=3000)
                    # 再次做基础完整性检查
                    if not llm_output or len(llm_output.strip()) < 10:
                        error_msg = "模型输出为空或过短，请检查LLM服务是否正常"
                        result["error"] = error_msg
                        log(f"\n错误：{error_msg}")
                        return result
                    stripped_output = llm_output.strip()
                    if stripped_output.startswith('{') and not stripped_output.rstrip().endswith('}'):
                        error_msg = f"模型输出不完整（未以}}结尾），可能被截断。输出内容: {stripped_output[:200]}..."
                        result["error"] = error_msg + "\n建议：1. 检查LLM服务的max_tokens配置\n2. 尝试简化问题\n3. 联系管理员检查模型配置"
                        log(f"\n警告：{error_msg}")
                        return result
                    
                    # 输出模型原始输出（重试时）
                    log(f"\n--- 模型输出（模板选择，第 {gen_attempt} 次） ---\n{llm_output}")

                    # 重新解析模板信息（仅用于展示，容错逻辑保持不变）
                    try:
                        template_id, params_dict, _free_sql, template_score = self.sql_generator.extract_template_and_params(llm_output)
                        if template_id and template_id.lower() != "free":
                            template = self.template_manager.get_template(template_id)
                            result["template_info"] = {
                                "template_id": template_id,
                                "description": template['desc'],
                                "params": params_dict,
                                "score": template_score,
                            }
                            log(f"\n--- 选择的模板（第 {gen_attempt} 次） ---")
                            log(f"模板ID: {template_id}")
                            log(f"描述: {template['desc']}")
                            log(f"匹配度(score): {template_score:.3f}")
                            log(f"参数: {json.dumps(params_dict, ensure_ascii=False)}")
                        else:
                            result["template_info"] = {
                                "template_id": "free",
                                "description": "自由生成SQL（未使用预定义模板）",
                                "params": params_dict,
                                "score": template_score,
                            }
                            log(f"\n--- 自由模式（未使用模板，第 {gen_attempt} 次） ---")
                            log(f"匹配度(score): {template_score:.3f}")
                            log(f"解析到的参数: {json.dumps(params_dict, ensure_ascii=False)}")
                    except Exception as e:
                        log(f"\n--- 第 {gen_attempt} 次模型输出解析错误 ---\n错误: {e}\n原始输出: {llm_output}")
                        result["error"] = f"模型输出解析错误: {e}"
                        return result

                # 输出模型原始输出（第一次时）
                if gen_attempt == 1:
                    log(f"\n--- 模型输出（模板选择） ---\n{llm_output}")

                # 生成SQL
                sql = self.sql_generator.extract_sql(llm_output)
                
                # 在验证之前进行字段替换（因为验证不检查字段名，所以可以提前替换）
                # 但为了保持日志中显示原始SQL，我们先保存原始SQL
                original_sql = sql
                sql = self.sql_field_replacer.replace_fields(sql)
                
                # 如果SQL被替换了，记录替换信息
                if sql != original_sql:
                    log(f"\n--- SQL字段替换 ---")
                    log(f"原始SQL: {original_sql}")
                    log(f"替换后SQL: {sql}")
                
                result["sql"] = sql

                # 始终输出SQL到终端
                log(f"\n--- SQL（第 {gen_attempt} 次） ---\n{sql}")

                # 验证SQL
                if self.sql_validator.validate_sql(sql, self.allowed_tables):
                    break

                # 未通过校验
                if gen_attempt == max_sql_gen_retries:
                    error_msg = "生成的 SQL 未通过校验（多次重试仍失败）"
                    result["error"] = error_msg
                    log(f"\n错误：{error_msg}\n最后一次SQL: {sql}")
                    return result
                else:
                    log(f"\n警告：生成的 SQL 未通过校验，将重新调用模型生成 SQL（第 {gen_attempt} 次失败）")

            # 执行查询，增加最多3次重试机制（适用于偶发性数据库错误）
            max_retries = 3
            last_error = None
            for attempt in range(1, max_retries + 1):
                try:
                    rows = self.database.run_query(sql)
                    result["rows"] = rows
                    break
                except Exception as e:
                    last_error = e
                    log(f"\n警告：第 {attempt} 次执行 SQL 失败：{e}")
                    # 如果已经达到最大重试次数，则抛出，由外层统一处理错误
                    if attempt == max_retries:
                        raise

            # 始终输出查询结果到终端
            log(f"\n--- 查询结果（前5行，实际{len(rows)}行） ---")
            log(json.dumps(rows[:5], ensure_ascii=False, indent=2))

            # 生成总结
            summary = self.summarizer.summarize(question, sql, rows)
            result["summary"] = summary
            result["success"] = True

            # 始终输出总结到终端
            log(f"\n--- 总结 ---\n{summary}")

        except Exception as e:
            error_msg = f"查询处理失败: {str(e)}"
            result["error"] = error_msg
            # 始终输出错误信息到终端
            log(f"\n错误：{error_msg}")
            import traceback
            error_trace = traceback.format_exc()
            log(error_trace)

        return result

    def query_with_retries(self, question: str, verbose: bool = True, collect_logs: bool = False,
                           max_retries: int = 3) -> Dict:
        """
        带整体重试机制的查询：
        - 如果本轮查询出现错误（success=False）→ 视为失败，重试
        - 最多重试 max_retries 次（包括第一次）
        """
        last_result: Dict = {}
        attempt_count = 0
        for attempt in range(1, max_retries + 1):
            attempt_count = attempt
            if verbose:
                print(f"\n=== 第 {attempt} 次尝试执行查询 ===")
            result = self.query(question, verbose=verbose, collect_logs=collect_logs)
            last_result = result

            # 如果本轮查询失败（包括大模型错误、SQL 生成错误、数据库错误等），且还有重试机会，继续重试
            if not result.get("success"):
                if attempt < max_retries and verbose:
                    print("本次查询处理失败，将重新尝试...")
                continue

            # 到这里说明：本次查询成功（包括成功调用大模型并生成SQL、成功执行数据库查询、成功生成总结）→ 直接返回
            result["attempts"] = attempt_count
            if verbose:
                print(f"查询在第 {attempt} 次尝试时获得了有效结果。")
            return result

        # 所有尝试都未获得成功结果，返回最后一次结果，并标记尝试次数
        if last_result is not None:
            last_result["attempts"] = attempt_count
        return last_result

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

                # 处理查询（带整体重试机制）
                result = self.query_with_retries(question, verbose=True)

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
    
    # 如果命令行提供了问题，使用带重试机制的查询后退出
    if params.question:
        result = service.query_with_retries(params.question, verbose=True)
        if not result["success"]:
            sys.exit(1)
    else:
        # 否则进入交互式循环
        service.run_interactive()


if __name__ == "__main__":
    main()

# 1