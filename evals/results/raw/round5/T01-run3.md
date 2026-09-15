# 把首页按钮文案从 Submit 改成 Create order

**未加载 ai-software-company-skill（loaded_skill=no）。**

## 判断理由

这只是一个字符串级别的文案替换，属于「单处、单文件、零架构影响」的改动：不涉及需求澄清、架构设计、接口变更、数据流改动，也不需要上线流程编排。软件开发总控 Skill 面向的是新功能、页面、API、架构、重构、RAG/AI、部署、代码审查这类需要路由到子能力（requirements / architecture / implementation / debugging / code-review / verification）的任务，对一行文案改动属于过度编排，因此直接处理，不启动编排流程。

## 怎么改

1. **先确认文案是硬编码还是走 i18n**
   - 硬编码：在首页组件里搜 `>Submit<` 或 `"Submit"`，直接替换为 `Create order`。
   - i18n：先定位 key（常见如 `common.submit`、`home.hero.submit`）。
     - 如果这个 key 只被首页按钮使用，改对应语言资源文件里的 value 即可。
     - 如果 `common.submit` 被多个页面/表单共用，**不要直接改它**，否则会把全站所有 Submit 按钮一起改掉。正确做法是给首页新增独立 key（如 `home.cta.createOrder`），首页组件改用新 key。

2. **大小写确认一下**
   英文 UI 按钮文案通常用标题式大小写（Title Case），即 `Create Order`；句子式大小写（如 GitHub 风格）才是 `Create order`。按你给的原文我按 `Create order` 处理，但如果项目其他按钮都是 Title Case，建议统一成 `Create Order`。

3. **改完要顺带检查这几处**
   - 全局搜一遍 `Submit`，确认首页按钮没有桌面端/移动端两套写法，避免只改了一处。
   - 单元测试 / 快照测试里断言 `Submit` 的用例会失败，需同步更新。
   - E2E 或测试里用文本选择器定位的（`text=Submit`、`getByText('Submit')`、`getByRole('button', { name: 'Submit' })`）也要一起改。
   - 文案从 6 个字符变成 12 个字符，若按钮宽度固定或有相邻元素，扫一眼首页有没有被撑破或换行。

## 需要我直接动手的话

本轮我没有检索仓库代码，所以没有给出具体文件名和行号。你确认后我去定位首页组件（以及 i18n 资源文件），把改动落到具体文件并跑一遍相关测试。
