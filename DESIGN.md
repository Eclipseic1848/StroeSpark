---
version: alpha
name: StoreSpark
description: 面向门店宣传任务的中文工作台，以清晰输入、可编辑内容和真实状态为核心。
colors:
  background: "#FFFFFF"
  surface: "#F5F7F7"
  primary: "#176B63"
  primary-hover: "#10564F"
  text: "#163B3B"
  muted: "#617174"
  border: "#DCE5E3"
  accent: "#D96B3B"
  danger: "#A13030"
  scrollbar: "#A4B8B3"
typography:
  sans:
    fontFamily: '"Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif'
    fontSize: "14px"
    lineHeight: "1.65"
rounded:
  DEFAULT: "8px"
  dialog: "12px"
spacing:
  page: "40px"
  mobile-page: "20px"
  section: "24px"
components:
  button:
    height: "44px"
  input:
    height: "46px"
  textarea:
    height: "120px"
---

# StoreSpark 界面设计

## Overview

工作台服务餐饮店主及门店、品牌运营人员。用户可以从一句经营诉求或已有素材开始，逐步形成宣传方向与可编辑文案。产品事实以 [产品定义](docs/product-definition.md)、[流程草案](docs/product-flow-draft.md)和后端 API 为准；界面不制造任务、生成结果或经营效果。

界面参考是安静的内容编辑台：左侧任务列表，右侧当前任务，明确的输入与交付区域。唯一表达性元素是深青与橙色相接的星形标记。避免营销首页、大幅插画、假指标和重复卡片。

目标语言为简体中文。当前验证平台为 Windows Chromium 的桌面和窄屏视口；手机真机和微信小程序不由本 Web 页面替代。

首版只有任务工作区与模型设置两个视图，没有删除操作或可检索的数据表，不另建多流程 UX 合同。以下组件与行为约定为当前规范。

视觉概念在 [工作台空态图](web/design/workspace-concept.png)中。它是助手提出的实现基准，尚未经商家验收。

运行时颜色、字体与间距的唯一实现源为 [styles.css](web/src/styles.css) 的全局变量与组件规则；本文件镜像已实施数值并记录意图。所有组件通过语义 CSS 变量使用颜色，未来修改需同步两处并复查渲染。

## Colors

背景使用纯白；淡灰绿色侧栏只用于区分导航。深青用于主操作、选择状态和焦点。橙色只出现在品牌标记；不将它用于无意义的标签。错误使用文字和红色边界同时表达，成功消息使用明确文案及淡绿色背景。

当前只有浅色主题。高对比度模式保留系统边界与可操作滚动条，不伪装已实现深色主题。

## Typography

中文正文与控件均使用 `sans` 字体栈，不下载外部字体。正文与输入 14px，辅助文字 12px，主要标题 27–36px，章节标题 19px。正文行高 1.65，模型长文本行高 1.85；重要内容允许换行，不依赖悬停查看完整值。

## Layout

桌面顶栏至少 68px；任务侧栏 248px；内容区四周通常为 40px。新建任务表单为主要焦点，右侧用连续文本解释三个交付物。任务详情将对话与内容编辑并列，形成输入与输出关系。

1200px 以下改为顺序布局，交付说明和内容编辑移到下方。800px 以下任务列表移到顶部，表单双列变单列。页面自然滚动，不给表单祖先固定视口高度；仅长对话和窄屏任务列表拥有受限滚动区域。

## Elevation & Depth

主要层级依赖留白、浅色分区和细边界。普通表单与内容区域不加悬浮阴影。未保存修改的确认框使用原生 `dialog.showModal()` 的隔离与焦点机制，外观由应用样式控制。

## Shapes

输入与按钮使用 8px 圆角；对话框 12px。细分隔线代替嵌套卡片。星形标记为小型 SVG，界面没有需要栅格资产的插画。

## Components

### 组件归属

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Form | `Shared.Field` 和 `Shared.TextField` | `DESIGN.md`、`storespark/schema.py` | 单行、自动增高多行 | `web/tests/workspace.spec.ts` 标签、错误关联、键盘 |
| Secret | `Shared.SecretField` | `DESIGN.md`、`storespark/provider.py` | 模型密钥、访问令牌 | `web/tests/workspace.spec.ts` 默认隐藏、可切换、不存模型密钥 |
| Toast | `Shared.Notice` | `DESIGN.md` | 提示、错误、成功 | `web/tests/workspace.spec.ts` status 或 alert 语义 |
| Scrollbar | `styles.css` 全局规则 | `DESIGN.md`、`web/src/styles.css` | 仅几何尺寸可按区域调整 | 标准属性及 Chromium 回退 |
| Unsaved changes | `App` 的应用对话框 | `DESIGN.md` | 继续编辑、放弃并离开 | `web/tests/workspace.spec.ts` Escape、焦点恢复、确认后导航 |
| CRUD | `api.ts` 与 `App` | `storespark/app.py`、`storespark/schema.py` | 新建、读取、模型动作、上传、编辑、导出 | `web/tests/workspace.spec.ts` 全流程与失败恢复 |

当前渠道与内容形式使用自由文本，不引入自定义下拉、日期选择或表格组件。处理动作使用原生单选控件，保持键盘行为。

### 操作与恢复

新建任务后进入该任务；失败时保留输入。素材先实际上传再显示为已保存；部分上传失败保留失败文件以便重试。模型动作在收到成功响应后才显示成功；错误时保留输入并读取后端已保留的沟通记录，不自动重试付费调用。

编辑内容后明确显示未保存状态，保存成功后才标为已保存。生成新文案及导出前需要先保存当前内容修改。切换视图或任务时，有未保存输入会触发应用确认框；刷新或关闭页面使用浏览器 `beforeunload` 机制。

模型 API 密钥仅停留在当前设置表单，提交后清空，不进入浏览器存储。用户明确连接后，工作台访问令牌仅放入 `sessionStorage`；它与模型密钥分开。401 显示恢复提示，处理中发生 401 不强制切走而丢失正在编辑的内容。

### 可访问性与状态

所有动作使用原生按钮、链接、文件输入与单选控件；每个字段有可点击标签。表单关闭原生校验气泡，提供中文提示并将焦点放到首个错误字段。主操作最小高度 44px；禁用、忙碌、悬停与焦点状态同时表达。

加载消息位于稳定区域，按钮忙碌时不改变尺寸。多行文本框禁止手动拖动，随内容增高，过长时内部滚动。减少动态效果偏好会关闭过渡。

## Do's and Don'ts

- 保持任务、素材与内容的真实状态；失败不能伪装完成。
- 需求明确时直接承接，不迫使用户重新进行整套访谈。
- 保留长内容的阅读与编辑空间，移动端不隐藏核心操作。
- 不渲染模型输出中的 HTML，不把上传素材默认公开。
- 不将文案或脚本标为海报图片、视频成片或已验证的进店效果。
