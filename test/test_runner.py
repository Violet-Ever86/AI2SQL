"""
测试脚本：批量运行测试问题并生成报告
使用方法: python test_runner.py
"""

import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import AI2SQLService

# 测试问题列表（重点测试新增关联关系）
TEST_QUESTIONS = [
    # 基础测试
    ("基础-1", "吕昊的个人信息"),
    ("基础-2", "带班记录BM-00056对应的注意事项？"),
    ("基础-3", "查询最近10条工作记录？"),
    ("基础-4", "罗康康从3月到11月的所有工作内容"),
    ("基础-5", "桂晓明最近干了什么"),
    ("基础-6", "桂编号dce4c9af-191c-c94d624-aa2f-7fae2adfdee2的人做了什么"),
    ("基础-7", "罗康康做了什么"),
    ("基础-8", "桂晓明最近干了什么"),
    ("基础-9", "谁的带班次数最多"),
    ("基础-10", "谁的跟班次数最多"),
    ("基础-11", "谁的工作次数最多"),
    ("基础-12", "三月份，哪个项目里的带班次数最多？请按项目统计每个项目的带班总次数，并按次数从高到低排序，取前 5 名"),
    ("基础-13", "三月份，哪个项目里的工作次数最多？请按项目统计每个项目的总次数，并按次数从高到低排序，取前 5 名，同时工作分为跟班和带班统计"),
    ("基础-13.1","三月份，哪个项目里的工作次数最多？请按项目统计每个项目的总次数，并按次数从高到低排序，取前 20 名，分给给出他们的带班和跟班次数"),
    ("基础-14", "工作次数最多的前三个人是谁？每个人工作了多少次"),
    ("基础-15", "罗康康带班和跟班次数分别是多少次"),
    ("基础-16", "岗位是‘单元长’的人员中，谁带班次数最多？列出前 3 名及各自的带班次数。"),
    ("基础-17", "2025 年全年，‘BM-00018’（所属项目为包含‘BM-00018）的人员中，综合工作量（带班+跟班次数之和）排名前 5 的人是谁？请给出他们的姓名、所属部门、带班次数、跟班次数和总次数。"),
    ("基础-18", "有没有人在同一天既带班又跟班？请列出这些日期、人员姓名，以及当天带班和跟班的作业内容"),
    ("基础-19", "有没有人在同一个工程上连续三天工作？请列出持续天数最多的工程名称、人员姓名和连续天数，连续工作开始结束时间，是跟班还是带班"),

    # 新增关联关系测试 - 责任单元
    ("新增-1", "罗康康从3月到11月的跟班作业中的班组对应的工作地方"),
    ("新增-2", "罗康康从3月到11月的跟班作业对应的班组长"),
    ("新增-3", "贵州春桥（下构班组）跟了哪些作业"),

    # 新增关联关系测试 - 管控计划
    ("新增-4", "2025年3月3号的管控计划有几个，每个的地点在哪"),
    ("新增-5", "2025年4月1号对门山隧道的管控计划详情"),
    ("新增-6", "跟班任务掌子面初期支护，仰拱衬砌的管控计划是几号"),



    #
    # # 新增关联关系测试 - 责任单元
    # ("新增-1", "罗康康从3月到11月的跟班作业中的班组对应的工作地方"),
    # ("新增-2", "罗康康从3月到11月的跟班作业对应的班组长"),
    # ("新增-3", "贵州春桥（下构班组）跟了哪些作业"),
    #
    # # 新增关联关系测试 - 管控计划
    # ("新增-4", "2025年3月3号的管控计划有几个，每个的地点在哪"),
    # ("新增-5", "管控计划内容240-7灌注的日期和状态"),
    # ("新增-6", "跟班任务掌子面初期支护，仰拱衬砌的管控计划是几号"),
    #

    #
    # # 新增关联关系测试 - 班组 ↔ 责任单元
    # ("新增-4", "查询所有班组及其负责的责任单元信息（包括单元名称、负责人、工程类型、状态）"),
    # ("新增-5", "查询状态为'施工'的责任单元对应的所有班组信息"),
    # ("新增-6", "查询工程类型为'桥梁工程'的责任单元对应的班组名称和班组长"),
    #
    # # 新增关联关系测试 - 跟班记录 ↔ 班组
    # ("新增-7", "查询最近跟班记录对应的班组信息和班组长联系方式"),
    # ("新增-8", "查询跟班记录中所有班组及其负责的责任单元信息"),
    # ("新增-9", "查询某条跟班记录对应的班组、班组长、以及该班组负责的责任单元名称"),
    #
    # # 复杂关联查询
    # ("复杂-1", "查询最近跟班记录，显示跟班人员、班组名称、班组长、责任单元名称、单元长姓名"),
    # ("复杂-2", "查询所有'施工'状态的责任单元及其对应的班组信息"),
    # ("复杂-3", "查询所有班组的班组长姓名和手机号"),
    # ("复杂-4", "查询某责任单元的班组信息，包括班组名称、班组长、手机号、班组成员、公司"),
]

def run_tests():
    """运行所有测试问题"""
    print("=" * 80)
    print("AI转SQL系统测试开始")
    print("=" * 80)
    
    service = AI2SQLService()
    results = []
    
    for test_id, question in TEST_QUESTIONS:
        print(f"\n{'='*80}")
        print(f"测试 [{test_id}]: {question}")
        print(f"{'='*80}")
        
        try:
            result = service.query(question)
            results.append({
                "test_id": test_id,
                "question": question,
                "success": result["success"],
                "sql": result["sql"],
                "error": result.get("error"),
                "row_count": len(result.get("rows", [])),
            })
            
            if result["success"]:
                print(f"✅ 测试 [{test_id}] 成功 - 返回 {result['row_count']} 条记录")
            else:
                print(f"❌ 测试 [{test_id}] 失败 - {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"❌ 测试 [{test_id}] 异常 - {str(e)}")
            results.append({
                "test_id": test_id,
                "question": question,
                "success": False,
                "error": str(e),
            })
    
    # 生成测试报告
    print("\n" + "=" * 80)
    print("测试报告")
    print("=" * 80)
    
    total = len(results)
    success = sum(1 for r in results if r.get("success", False))
    failed = total - success
    
    print(f"总测试数: {total}")
    print(f"成功: {success} ({success/total*100:.1f}%)")
    print(f"失败: {failed} ({failed/total*100:.1f}%)")
    
    if failed > 0:
        print("\n失败的测试:")
        for r in results:
            if not r.get("success", False):
                print(f"  - [{r['test_id']}] {r['question']}")
                if r.get("error"):
                    print(f"    错误: {r['error']}")
    
    # 保存详细报告到文件
    report_file = "test_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total": total,
                "success": success,
                "failed": failed,
                "success_rate": f"{success/total*100:.1f}%"
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细报告已保存到: {report_file}")
    
    return success == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

