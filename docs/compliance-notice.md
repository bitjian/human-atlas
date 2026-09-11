# 合规声明与署名 / Compliance Notice & Attribution

> 本文件面向对外使用场景：可整体或分段用于产品「关于」页、销售页、客户尽调材料、采购合同附件。
> 文中的 `[运营主体]`、`[产品名称]`、`[联系邮箱]` 为占位符，请替换为实际信息。

---

## 一、许可概览 / License Overview

| 组成部分 | 权利人 | 许可协议 | 商用 | 转售 | 修改 | 义务 |
|---|---|---|---|---|---|---|
| 应用程序代码 | ashemag | MIT License | ✅ | ✅ | ✅ | 保留版权声明与许可文本 |
| 解剖数据集 | The Database Center for Life Science | CC BY 4.0 | ✅ | ✅ | ✅ | 署名、附许可链接、标明改动、不暗示背书 |

**结论：本项目所用上游资源均明确允许商业使用与转售，使用方仅承担署名义务，无付费、无开源传染义务。**

---

## 二、署名声明 / Attribution Notice（对外展示版）

### 中文

本产品基于开源项目 [ashemag/human-atlas](https://github.com/ashemag/human-atlas)（MIT License，版权所有 © 2026 ashemag）构建。

解剖数据来源：**BodyParts3D**，版权所有 © The Database Center for Life Science，依 **CC BY 4.0 国际许可协议**使用。
许可协议：https://creativecommons.org/licenses/by/4.0/
数据集出处：https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html

本版本由 `[运营主体]` 在原作基础上进行改编（详见第四节），改编部分的权利归 `[运营主体]` 所有；未修改部分仍遵循其原始许可协议。

### English

This product is built upon the open-source project [ashemag/human-atlas](https://github.com/ashemag/human-atlas) (MIT License, Copyright © 2026 ashemag).

Anatomy data source: **BodyParts3D**, © The Database Center for Life Science, used under the **CC BY 4.0 International** license.
License: https://creativecommons.org/licenses/by/4.0/
Dataset: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html

This version is an adaptation by `[运营主体]` (see Section 4). Rights in the adapted portions belong to `[运营主体]`; unmodified portions remain under their original licenses.

---

## 三、免责声明 / Disclaimer（对外展示版）

### 中文

本产品为**三维解剖学参考工具，仅供教学、科普与一般性了解用途**。

- 本产品**不构成医疗建议**，不能替代执业医师的专业判断。
- 本产品**不得用于临床诊断、治疗规划、手术导航或任何医疗决策场景**。
- 三维模型为参考解剖的简化表示，不代表任何具体个体的真实解剖结构，亦不包含人体的全部结构或变异。
- 本产品按「现状」提供，不附带任何明示或默示的担保。

如将本产品用于医疗、教育考核或任何专业场景，使用方应自行评估适用性并承担相应责任。

### English

This product is a **3D anatomical reference tool intended solely for education, general interest, and illustrative purposes**.

- It **does not constitute medical advice** and is not a substitute for professional medical judgment.
- It **must not be used for clinical diagnosis, treatment planning, surgical navigation, or any medical decision-making**.
- The 3D models are simplified representations of reference anatomy. They do not depict any specific individual and do not include every human structure or variation.
- The product is provided "as is", without warranty of any kind, express or implied.

Users deploying this product in medical, educational-assessment, or other professional contexts are responsible for independently evaluating its fitness and assume all associated risk.

---

## 四、改编说明 / Statement of Changes

依 CC BY 4.0 第 3(a)(1)(B) 条要求，特此标明对原始作品所做的改动：

| 改动项 | 说明 |
|---|---|
| 用户界面中文化 | 全部界面文案翻译为简体中文，新增中英文实时切换 |
| 解剖术语中文化 | 为 5,566 个解剖概念/部件中的 98.2% 提供中文译名，未收录部分回退英文原名 |
| 交互调整 | 新增结构详情返回上级导航、搜索清空、系统图层选择持久化等 |
| 排版适配 | 中文语境下的字体栈与字距调整 |

**未改动的部分**：三维几何数据、解剖层级结构（FMA 概念体系）、原始英文名称与元数据保持不变。

---

## 五、商用合规清单 / Commercial Use Checklist

发布或销售前逐项确认：

- [ ] 部署产物中包含 `LICENSE` 文件（含 `Copyright (c) 2026 ashemag`，不得删除或替换为自有版权）
- [ ] 部署产物中包含 `ATTRIBUTION.md`（BodyParts3D 署名、许可链接、数据集出处）
- [ ] 产品「关于」页展示署名声明（第二节内容）
- [ ] 产品首页或页脚可见位置展示免责声明（第三节内容）
- [ ] 已标明本产品为改编版本（第四节内容）
- [ ] 产品名称**未使用** "Human Atlas" 或与上游混淆的名称
- [ ] 宣传材料中**未暗示**与原作者存在官方合作、授权或背书关系
- [ ] 如交付给客户，交付文档附本合规声明
- [ ] 如目标客户含医疗机构，已单独评估用途合规性（见第六节）

---

## 六、风险提示 / Risk Notes

| 级别 | 事项 | 处理建议 |
|---|---|---|
| 🔴 高 | 用于临床/诊断场景 | 可能触发医疗器械监管（如中国 NMPA 备案/注册要求）。合规做法：产品定位明确为教学科普，合同中排除医疗用途 |
| 🔴 高 | 删除或隐藏署名 | 同时违反 MIT 与 CC BY 4.0，权利人可主张侵权 |
| 🟡 中 | 使用 "Human Atlas" 作为产品名 | MIT 不授予商标许可，建议另行命名 |
| 🟡 中 | 未标明改编事实 | CC BY 4.0 明文要求，缺失即构成违约 |
| 🟢 低 | 第三方依赖许可 | `three.js` 等依赖多为 MIT，随包保留许可即可 |

**遗留许可问题的处理说明**：BodyParts3D 源文件注释中残留有旧版 *CC BY-SA 2.1 Japan* 条款。官方现行许可页（2025-02-27 更新）已明确以 **CC BY 4.0** 覆盖该遗留文本，并明示允许再分发与改编。建议留存许可页面存档（截图或 PDF）作为尽调依据。

---

## 七、声明

本文件基于相关许可协议文本整理，供合规参考，不构成正式法律意见。若涉及公司主体运营、机构采购合同或医疗相关场景，建议就**产品名称、免责条款、数据用途声明**三项另行咨询专业法律顾问。

---

`[运营主体]`
`[联系邮箱]`
最后更新：2026-09-11
