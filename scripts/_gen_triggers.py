#!/usr/bin/env python3
"""One-off: emit evals/triggers/ (10 must-fire + 10 must-not-fire), then delete itself."""

import os

FIRE = [
    dict(
        n="01", slug="change-button-text", title="改按钮文案",
        route="implementation → verification",
        prompt="「把首页那个按钮的文案从 Submit 改成 Create order。」",
        why="真实的代码交付：改代码、有影响面（埋点 / 截图基线）、需要验证。",
        evidence=["说出任务级别", "点名要走的 Skill", "输出验证方式或剩余风险"],
    ),
    dict(
        n="02", slug="add-login", title="加登录",
        route="requirements → architecture → implementation → verification",
        prompt="「给我这个项目加个登录功能。」",
        why="中任务 + 含鉴权，按分级表强制安全审查。这是 ASCOS 最典型的场景。",
        evidence=["先补全需求再说实现", "提到安全审查", "提到会话 / 口令存储 / 防枚举"],
    ),
    dict(
        n="03", slug="prod-500", title="线上 500",
        route="debugging → code-review → verification",
        prompt="「下单接口偶尔 500，日志里有 NullPointerException，帮我看看。」",
        why="Bug 报修必须走独立调试流程，不能直接猜着改。",
        evidence=["先要复现或反馈环", "提到证据级别", "区分根因与猜测"],
    ),
    dict(
        n="04", slug="greenfield", title="从零搭项目",
        route="requirements → architecture → implementation → verification",
        prompt="「我要做一个 SaaS，帮我从零搭起来。」",
        why="大任务，必须走完整链路；且要问清架构分叉点，不能闷头写。",
        evidence=["先问清业务边界", "提到模块 / 接口设计", "要求 Build / Test 真实证据"],
    ),
    dict(
        n="05", slug="payment", title="接支付",
        route="requirements → architecture → implementation → verification",
        prompt="「接一下微信支付。」",
        why="含支付：强制安全审查；回调幂等、验签、对账缺一不可。",
        evidence=["提到回调验签或幂等", "提到密钥走环境变量", "提到金额以服务端为准"],
    ),
    dict(
        n="06", slug="modularize-monolith", title="拆单体",
        route="architecture → implementation → verification",
        prompt="「现在这个单体太乱了，帮我拆成模块清晰一点的结构。」",
        why="跨模块重构，需要变更影响分析和架构判据，不是简单移动文件。",
        evidence=["先做变更影响分析", "提到 seam / 接口 / 深模块", "默认选更简单的一侧"],
    ),
    dict(
        n="07", slug="pagination-search", title="列表分页搜索",
        route="requirements → implementation → verification",
        prompt="「给订单列表加分页和关键字搜索。」",
        why="中任务，需要补全边界（深翻页、空结果、注入）并验证。",
        evidence=["提到空数据 / 加载中 / 报错 / 无权限", "提到深翻页或索引", "有真实验证命令"],
    ),
    dict(
        n="08", slug="review-diff", title="审查这个 diff",
        route="code-review → verification",
        prompt="「帮我 review 一下这次的改动，看看有什么问题。」",
        why="明确的代码审查请求，走双轴审查（Standards vs Spec）。",
        evidence=["先固定对比基点", "按 Standards / Spec 分轴", "缺陷优先排序"],
    ),
    dict(
        n="09", slug="deploy-incident", title="上线后出问题",
        route="debugging → verification",
        prompt="「刚上线的版本，用户反馈打开就白屏，帮我查一下。」",
        why="线上问题：既要调试，也要走发布检查 / 回滚判据。",
        evidence=["先看日志 / 产物而不是猜", "提到回滚或发布检查", "给出证据级别"],
    ),
    dict(
        n="10", slug="crud-api", title="加一个 CRUD 接口",
        route="requirements → implementation → code-review → verification",
        prompt="「加一个商品的增删改查接口。」",
        why="契约先行的典型中任务，不该一上来就写 controller。",
        evidence=["先定接口契约", "提到参数校验或错误码统一", "有测试三场景"],
    ),
]

NOT_FIRE = [
    dict(
        n="11", slug="sql-tutorial", title="写 SQL 教程", near_miss="知识输出",
        prompt="「写一份 SQL 教程，讲清楚 JOIN 的几种类型。」",
        why="这是知识输出，不是交付软件。没有代码库、没有产物、没有验证，拉起完整开发链纯属自嗨。",
        evidence=["直接讲 JOIN", "没有任务分级", "没有路由推演"],
    ),
    dict(
        n="12", slug="explain-deep-module", title="解释什么是深模块", near_miss="概念问答",
        prompt="「深模块是什么意思？和普通的分层有什么区别？」",
        why="用户问的是概念，不是要做架构。ASCOS 自己的术语出现在问题里，最容易误触发 —— 这条专门测这个。",
        evidence=["直接解释概念", "没有开始做架构设计", "没有产出 ADR"],
    ),
    dict(
        n="13", slug="polish-copy", title="润色一段文案", near_miss="纯文案",
        prompt="「帮我把这段产品介绍润色一下，读起来更顺。」",
        why="纯文案润色，不涉及代码交付（README 的 Not for 已明确排除）。",
        evidence=["直接给出润色结果", "没有任务分级", "没有 DoD 或风险清单"],
    ),
    dict(
        n="14", slug="delay-apology-email", title="写给客户的延期邮件", near_miss="沟通协作",
        prompt="「帮我写一封给客户的邮件，说明这次交付要延期一周。」",
        why="排期与人员沟通，明确在 Not for 里。写成软件交付流程会显得荒谬。",
        evidence=["直接给邮件草稿", "没有拉起开发链", "没有技术方案"],
    ),
    dict(
        n="15", slug="translate-doc", title="翻译文档", near_miss="翻译",
        prompt="「把这份英文 API 文档翻译成中文。」",
        why="翻译不是软件交付，没有需要验证的产物。",
        evidence=["直接给译文", "没有任务分级", "没有验证步骤"],
    ),
    dict(
        n="16", slug="rebase-vs-merge", title="rebase 和 merge 的区别", near_miss="工具用法咨询",
        prompt="「Git rebase 和 merge 到底有什么区别？我该用哪个？」",
        why="工具用法咨询，通用知识问答。答完即可，无需路由到任何能力 Skill。",
        evidence=["直接对比两者", "给出选择建议", "没有开始改代码"],
    ),
    dict(
        n="17", slug="summarize-article", title="总结这篇文章", near_miss="信息处理",
        prompt="「帮我总结一下这篇文章的核心观点。」",
        why="信息处理，不是交付软件。",
        evidence=["直接给摘要", "没有路由推演", "没有风险清单"],
    ),
    dict(
        n="18", slug="name-the-project", title="起个项目名", near_miss="创意发散",
        prompt="「帮我想几个项目名字，做团队协作工具的。」",
        why="创意发散，没有可验证的交付物。",
        evidence=["直接给候选名字", "没有任务分级", "没有 PRD"],
    ),
    dict(
        n="19", slug="meeting-notes", title="整理会议纪要", near_miss="文档整理",
        prompt="「这是今天评审会的记录，帮我整理成会议纪要。」",
        why="文档整理。即使会议内容是技术讨论，交付物也不是软件。",
        evidence=["直接给纪要", "没有路由推演", "没有 DoD"],
    ),
    dict(
        n="20", slug="how-to-use-lib", title="axios 怎么设超时", near_miss="API 用法咨询",
        prompt="「axios 怎么设置请求超时？」",
        why="单点 API 用法咨询。即使答案里含代码片段，它也不是一次软件交付。",
        evidence=["直接给用法", "没有任务分级", "没有拉起完整开发链"],
    ),
]

os.makedirs("evals/triggers", exist_ok=True)


def render(c: dict, fire: bool) -> str:
    lines = ["---", "id: T%s" % c["n"], "group: trigger",
             "expect: %s" % ("fire" if fire else "not_fire")]
    if fire:
        lines.append("route: %s" % c["route"])
    else:
        lines.append("near_miss: %s" % c["near_miss"])
    lines.append("evidence:")
    for e in c["evidence"]:
        lines.append("  - %s" % e)
    lines += ["---", "", "# T%s · %s" % (c["n"], c["title"]), "", "## 输入",
              c["prompt"], "", "## 为什么%s" % ("必须触发" if fire else "不能触发"),
              c["why"], "", "## 判定"]
    if fire:
        lines += [
            "- [ ] 出现下列 evidence 至少一项（说明 ASCOS 真的接管了，不是裸模型在答）",
            "- [ ] **触发不等于上全套**：小任务不得因此产出 PRD / ADR / TEST_PLAN",
        ]
    else:
        lines += [
            "- [ ] 直接回答问题，没有出现任务分级或路由推演",
            "- [ ] 没有产出 PRD / ADR / TEST_PLAN / DoD / 剩余风险清单",
            "- [ ] 没有拉起 13 个角色视角",
            "- [ ] 出现下列 evidence 至少一项（说明它当成普通问答处理了）",
        ]
    lines += ["", "## evidence（阅卷锚点，不是字符串匹配）"]
    for e in c["evidence"]:
        lines.append("- %s" % e)
    return "\n".join(lines) + "\n"


count = 0
for c in FIRE:
    open(os.path.join("evals/triggers", "%s-%s.md" % (c["n"], c["slug"])), "w",
         encoding="utf-8").write(render(c, True))
    count += 1
for c in NOT_FIRE:
    open(os.path.join("evals/triggers", "%s-%s.md" % (c["n"], c["slug"])), "w",
         encoding="utf-8").write(render(c, False))
    count += 1

print("wrote %d trigger cases" % count)
