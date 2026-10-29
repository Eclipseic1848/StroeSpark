**品牌、快消、零售与餐饮内容制作 Skills 和模板调研**

核验日期：2026年10月26日。

本次筛选出13个GitHub项目，覆盖品牌口径、内容策划、广告文案、中文图文、商品详情、餐饮门店内容和会员营销。具体能力以当前仓库中的SKILL.md、模板及相关脚本为准；下文的行业适配与优先顺序是选型分析，尚未经过品牌实际生产或投放验证。

最值得先试的组合是：品牌与广告用marketingskills，中文图文用baoyu-skills，商品详情用writer/skills或eCommerce-Skills，餐饮内容参考ai-restaurant-claude。固定品牌模板可从content-skills的品牌文件模板起步。餐饮专用项目普遍规模较小，应先作为试用或流程素材。

**1. coreyhaines31/marketingskills：品牌口径、广告创意与营销文案**

具体资源：

- [product-marketing](https://github.com/coreyhaines31/marketingskills/blob/main/skills/product-marketing/SKILL.md)：整理产品、受众、定位、客户语言、品牌语气、卖点证据和目标，形成后续Skill共用的产品营销底稿。
- [content-strategy](https://github.com/coreyhaines31/marketingskills/blob/main/skills/content-strategy/SKILL.md)：内容支柱、优先选题、购买阶段与主题关系。
- [copywriting](https://github.com/coreyhaines31/marketingskills/blob/main/skills/copywriting/SKILL.md)：品牌官网、活动页、落地页的标题、主体和行动按钮文案。
- [ad-creative](https://github.com/coreyhaines31/marketingskills/blob/main/skills/ad-creative/SKILL.md)：多角度广告标题、正文、静态创意和短视频制作brief；可根据实际表现数据迭代。
- [social](https://github.com/coreyhaines31/marketingskills/blob/main/skills/social/SKILL.md)：社交贴文、轮播结构、内容日历、短视频脚本和一稿多用。
- [influencer-marketing](https://github.com/coreyhaines31/marketingskills/blob/main/skills/influencer-marketing/SKILL.md)：寄样、试用、达人合作、UGC内容brief和交付检查。

可直接取用的[静态广告模板库](https://github.com/coreyhaines31/marketingskills/blob/main/skills/ad-creative/references/static-ad-templates.md)包含实物DTC商品的成分/功能亮点、问题解决、创始人故事、评论和对比等结构。适合饮料、食品、日化、美妆等快消品，也可迁移到餐饮新品、套餐和主厨故事。

价值在于先统一品牌事实，再形成一组能交给设计师、摄影师或图片工具的创意。局限是渠道重点偏Meta、Google、Instagram、TikTok等；小红书、抖音和国内到店链路需要补充。文案和brief不等于图片或视频成片，模板的经验排名不代表本品牌实际效果。

**2. alirezarezvani/claude-skills：品牌规范、长文生产和内容brief模板**

[brand-guidelines](https://github.com/alirezarezvani/claude-skills/blob/main/marketing-skill/skills/brand-guidelines/SKILL.md)提供品牌审查、色彩使用、字体层级、语气矩阵和简版指南；[content-production](https://github.com/alirezarezvani/claude-skills/blob/main/marketing-skill/skills/content-production/SKILL.md)覆盖调研、brief、大纲、初稿及编辑检查。可直接参考[内容brief模板](https://github.com/alirezarezvani/claude-skills/blob/main/marketing-skill/skills/content-production/templates/content-brief-template.md)。

适合品牌故事、产品知识、选购指南、原料/工艺文章和餐饮主厨故事，也适合把连锁门店的视觉及语气验收要求写清楚。它更偏长内容，默认角色有B2B SaaS及技术内容倾向，需要替换为真实消费者场景。

现有[content-creator](https://github.com/alirezarezvani/claude-skills/blob/main/marketing-skill/skills/content-creator/SKILL.md)已标记废弃，写作应选content-production。其[品牌语气分析脚本](https://github.com/alirezarezvani/claude-skills/blob/main/marketing-skill/skills/content-production/scripts/brand_voice_analyzer.py)依赖英文词表、空格分词和英文可读性公式，不能直接把评分当成中文内容质量结论。品牌规范中的示例资产也需要替换。

**3. JimLiu/baoyu-skills：中文品牌图文与文章配图**

具体资源：

- [baoyu-xhs-images](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-xhs-images/SKILL.md)：把资料拆成1—10张连续图文卡片，生成大纲、逐图提示词和图片。
- [baoyu-cover-image](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-cover-image/SKILL.md)：文章封面与活动主题视觉草稿。
- [baoyu-infographic](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-infographic/SKILL.md)：产品比较、工艺流程、知识说明等信息图。
- [baoyu-article-illustrator](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-article-illustrator/SKILL.md)：按文章段落规划配图并插回正文。

适合新品种草、口味对比、套餐解读、零售选购清单、会员权益和食材知识。中文内容适配较直接，尤其适合先确定结构、再成套出图。需要公众号收尾时，可另接[baoyu-post-to-wechat](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-post-to-wechat/SKILL.md)排版并送草稿箱；草稿箱不等于已经群发。

图片生成需要可用后端，成本取决于所接服务。输出主要是位图，包装、Logo、菜品外观、价格和图内文字仍需验图；参考图不能保证严格锁定品牌资产。真实门店、工厂和菜品摄影也不能由生成图替代。

**4. social-media-skills/skills：短视频脚本、节点排期和品牌模板规划**

[short-form-video-script](https://github.com/social-media-skills/skills/blob/main/skills/short-form-video-script/SKILL.md)输出口播、屏幕文字、镜头节奏、开场备选和行动引导；[content-calendar](https://github.com/social-media-skills/skills/blob/main/skills/content-calendar/SKILL.md)建立持续排期结构；[seasonal-and-moment-marketing](https://github.com/social-media-skills/skills/blob/main/skills/seasonal-and-moment-marketing/SKILL.md)筛选适合品牌的季节与商业节点；[design-and-templates](https://github.com/social-media-skills/skills/blob/main/skills/design-and-templates/SKILL.md)规划品牌色、字体、版式和一组可复用模板。

适合快消开箱、产品演示、门店幕后、厨房过程、季节上新和节日活动。它把内容节奏、脚本和视觉规则串起来，便于团队重复生产。

短视频Skill交付可拍摄脚本，不能直接出成片；设计Skill交付模板系统规格，实际图形要在设计或图片工具中完成。默认平台和节日背景偏海外；文档中的发帖频次、留存指标和工具效果数字应作为待验证经验，不能直接作为本地经营目标。[仓库说明](https://github.com/social-media-skills/skills/blob/main/README.md)

**5. writer/skills：有商品事实约束的详情页与快消渠道材料**

[pdp-content](https://github.com/writer/skills/blob/main/skills/pdp-content/SKILL.md)从SKU属性、包装、规格书和获准宣称出发，输出商品标题、卖点、描述、规格、FAQ、图片替代文字及商品feed相关内容；缺属性进入缺口清单，冲突不静默补齐。适合多SKU快消、品牌官网和零售商商品页，是本次商品内容候选中事实约束写得较细的一项。

[retailer-jbp-and-line-review](https://github.com/writer/skills/blob/main/skills/retailer-jbp-and-line-review/SKILL.md)则面向品牌卖给零售商的场景，输出品类故事、上新提案、渠道评审材料和促销复盘。它适合KA/渠道销售内容，不属于面向消费者的种草制作。

仓库当前以企业销售及营销为主，不宜整体当成消费内容套件。商品与渠道规则重点偏美国及欧洲，需要补中国市场、平台和品牌自己的获准措辞；仓库关注度仍小，先试用更稳妥。[当前README](https://github.com/writer/skills/blob/main/README.md)

**6. nexscope-ai/eCommerce-Skills：商品描述、品类内容月历与复购邮件**

- [product-description-generator](https://github.com/nexscope-ai/eCommerce-Skills/blob/main/product-description-generator/SKILL.md)：商品标题、卖点、说明、标签、关键词覆盖与渠道格式。
- [ecommerce-content-marketing](https://github.com/nexscope-ai/eCommerce-Skills/blob/main/ecommerce-content-marketing/SKILL.md)：从评论与顾客痛点整理内容主线、逐周选题、开场文案和视觉方向。
- [ecommerce-email-marketing-builder](https://github.com/nexscope-ai/eCommerce-Skills/blob/main/ecommerce-email-marketing-builder/SKILL.md)：欢迎、弃购、购买后、交叉销售、补货、VIP和唤回等邮件流。

适合跨境零售和有消耗周期的咖啡、护肤、宠物食品、日用品品牌。优势是把商品属性、消费场景和生命周期内容接起来，不停留在孤立文案。

主要覆盖Shopify、Amazon、TikTok Shop等渠道，没有现成的天猫、京东、美团规范。商品示例含缺少来源的效果扩写，使用时必须限制为已确认事实。年度邮件日历也含旧年份日期，不能原样用于2026排程。输出流程说明不等于已接通邮件平台。

**7. CosmoBlk/email-marketing-bible：会员与消费者生命周期内容**

[核心Skill](https://github.com/CosmoBlk/email-marketing-bible/blob/main/SKILL.md)和[行业playbook](https://github.com/CosmoBlk/email-marketing-bible/blob/main/references/playbooks.md)覆盖营销邮件、品牌语气、欢迎、弃购、唤回和设计参考。DTC部分较深入；零售、餐饮条目确实存在，但只是简短行业摘要。

适合咖啡品牌复购、会员零售、生日/VIP、积分提醒和餐饮老客唤回。有现成邮件体系的团队更容易使用。其设计部分是参考案例及制作方向，并非一整包可直接下载的中文HTML模板。[设计参考](https://github.com/CosmoBlk/email-marketing-bible/blob/main/references/design.md)

国内企微、公众号、短信需要改写触达形式与节奏；不能直接等同于私域全渠道系统。作者同时经营邮件平台，选型比较应结合该商业背景判断。

**8. zubair-trabzada/ai-restaurant-claude：餐饮月历、广告文案和菜品拍摄brief**

- [restaurant-social](https://github.com/zubair-trabzada/ai-restaurant-claude/blob/main/skills/restaurant-social/SKILL.md)：30天社交选题、视觉brief、文案、标签和行动引导。
- [restaurant-ads](https://github.com/zubair-trabzada/ai-restaurant-claude/blob/main/skills/restaurant-ads/SKILL.md)：午餐、周末、配送、生日、新菜等10类广告角度，每类两版文案。
- [restaurant-photos](https://github.com/zubair-trabzada/ai-restaurant-claude/blob/main/skills/restaurant-photos/SKILL.md)：按菜品规划角度、光线、道具和镜头清单，供摄影师使用。

这三项比泛营销工具更贴近餐厅日常内容生产，适合菜品上新、工作日促销、主理人故事和一轮拍摄多次使用。摄影Skill只交付拍摄指导，不等于已经拍图或生图。

默认英语及美国市场，需替换为真实菜单、员工、门店、价格与活动。示例中的故事、评论、折扣和固定增长目标不能当作商家事实；仓库规模较小，宜用真实门店资料做样稿验证。

**9. miron-tech/restaurant-claude-skills：餐饮周内容和菜单描述模板**

[local-buzz](https://github.com/miron-tech/restaurant-claude-skills/blob/main/.claudeskills/local-buzz-SKILL.md)包含每周内容日历、节庆活动时间线、Google商家帖子、邮件、短信和活动邀请模板，适合单店或小连锁的淡日活动、节日套餐、门店故事。

[menu-engineer](https://github.com/miron-tech/restaurant-claude-skills/blob/main/.claudeskills/menu-engineer-SKILL.md)可单独使用菜单描述改写分支，强调口感、烹饪方式和关键食材；成本与定价分析不属于本次内容制作推荐范围。

行业相关度高，但仅小规模项目，主要面向美国市场，也不出图、不设计实体菜单、不发布。菜单示例存在自行增加食材、产地和工艺的情况，应只借描述结构，严格锁定真实配方。文件采用自定义.claudeskills布局，不能假设所有宿主都会自动发现。

**10. vstorm-co/content-skills：可复用的品牌基础文档模板**

[content-setup](https://github.com/vstorm-co/content-skills/blob/main/skills/content-setup/SKILL.md)通过品牌访谈建立三份共享资料：[BRAND.md模板](https://github.com/vstorm-co/content-skills/blob/main/skills/content-setup/templates/BRAND.md.template)、[VOICE.md模板](https://github.com/vstorm-co/content-skills/blob/main/skills/content-setup/templates/VOICE.md.template)和[VISUAL.md模板](https://github.com/vstorm-co/content-skills/blob/main/skills/content-setup/templates/VISUAL.md.template)。分别记录品牌是谁、怎样表达、视觉如何统一。

对同时管理多个品牌或多个门店账号的团队，这组模板的复用价值大：把受众、语气、禁用词、Logo、颜色、字体与例句写成后续任务可读的底稿。无需先采用整套内容工作室，也能从模板结构起步。

仓库内容示例偏技术和海外平台，需重写消费者字段。README中的行业数字与“去AI感”效果没有在本次得到独立支持；该项目的优势应理解为品牌资料组织方式，而非效果保证。默认安装脚本面向macOS/Linux，Windows实际安装未验证。[README](https://github.com/vstorm-co/content-skills/blob/main/README.md)

**11. LinkRogers/xhs-note-creator：HTML/CSS小红书卡片模板**

[Skill](https://github.com/LinkRogers/xhs-note-creator/blob/master/SKILL.md)把需求转成标题、正文、标签和卡片Markdown，再由[HTML模板](https://github.com/LinkRogers/xhs-note-creator/blob/master/assets/card.html)及Playwright渲染为封面和内容卡片。适合会员权益、参数对比、零售清单、餐饮套餐和营业信息。

它的价值是文字由浏览器排版，品牌色和字体可在CSS中控制；对价格、规则等密集文字，比完全让绘图模型生成文字更容易约束。但默认主题并非品牌专用设计，也不会自动获得真实商品摄影。

目前只有少量关注，最近推送停留在2026年2月。README自称MIT，仓库API未识别许可证，复用前需核对正式许可。其自动登录及Cookie流程不宜直接带进企业内容库；可先单独研究本地图文渲染部分。[README](https://github.com/LinkRogers/xhs-note-creator/blob/master/README.md)

**12. seedream0311-ai/restaurant-retail-content-flow：餐饮零售一稿多用流程参考**

[实际Skill](https://github.com/seedream0311-ai/restaurant-retail-content-flow/blob/main/skills/restaurant-retail-content-flow/SKILL.md)组织了“共同事实表→约500—800中文字文章→FB/IG/Threads/LINE文案→图像提示及状态→30—45秒短视频分镜”的流程。缺价格、优惠或营养事实时不自动补造，素材与成片边界比较清楚。

适合社区零售、餐饮菜单/午餐外带、主理人商店等场景，也适合借鉴为团队内容交付清单。默认繁体中文和台湾常用渠道，需要改成自己的语言与渠道。

图片生成和发布依赖外部工具，视频产物是脚本。仓库0星且未见LICENSE，宜列为流程研究参考，不能按成熟商用开源套件推荐；复制或分发前须确认许可。[仓库](https://github.com/seedream0311-ai/restaurant-retail-content-flow)

**13. xinyuxinsheng/douyin-local-ops-skill：国内门店内容与经营复盘框架**

[实际Skill](https://github.com/xinyuxinsheng/douyin-local-ops-skill/blob/main/SKILL.md)覆盖商家档案、诊断、三段短视频骨架、周复盘和内容模式沉淀。对国内餐饮与零售门店，POI、团购和核销链路比海外社交框架更贴近实际。

不过当前内容制作只包含基本脚本结构，文件明确把content-playbook、达人运营和本地投放详细SOP列为后续批次。它应归为门店运营参考，不能宣传为已经完成的内容生产套件。仓库3星、未见LICENSE，复用许可仍需确认。[README](https://github.com/xinyuxinsheng/douyin-local-ops-skill/blob/main/README.md)

**按实际任务选择**

| 当前需求 | 优先候选 | 应准备的资料 |
|---|---|---|
| 快消新品的一整组内容 | marketingskills + baoyu-skills | 品牌口径、真实卖点、包装图、消费者场景 |
| 多SKU商品上架与改写 | writer/pdp-content + nexscope商品描述 | SKU属性表、规格、包装、获准宣称、平台要求 |
| 餐饮新品与门店活动 | restaurant-social/ads/photos + baoyu-skills | 菜单、真实菜图、门店、价格、活动条件 |
| 达人试用与探店brief | influencer-marketing | 合作目标、交付物、必讲事实、禁用宣称和素材权利 |
| 品牌长期内容口径 | product-marketing + BRAND/VOICE/VISUAL模板 | 品牌定位、历史好稿、语气样本、VI资产 |
| 咖啡等消耗品复购与会员 | nexscope邮件流 + email-marketing-bible | 真实购买周期、会员规则、渠道和用户分组 |
| 国内门店抖音运营流程 | douyin-local-ops作框架参考 | 商家后台截图、团购信息、核销数据、现有素材 |

**仓库元数据快照**

星数仅反映关注度；许可证以仓库当前信息为线索，不构成授权审查。最近推送按UTC日期记录，不等同于正式发布或长期维护承诺。

| 仓库及元数据来源 | Stars | 最近推送 | 许可证线索 |
|---|---:|---|---|
| [marketingskills](https://api.github.com/repos/coreyhaines31/marketingskills) | 56,578 | 2026-10-22 | MIT |
| [alirezarezvani/claude-skills](https://api.github.com/repos/alirezarezvani/claude-skills) | 28,737 | 2026-10-23 | MIT |
| [baoyu-skills](https://api.github.com/repos/JimLiu/baoyu-skills) | 26,964 | 2026-09-10 | MIT |
| [social-media-skills/skills](https://api.github.com/repos/social-media-skills/skills) | 199 | 2026-10-15 | MIT |
| [writer/skills](https://api.github.com/repos/writer/skills) | 9 | 2026-10-21 | CC0-1.0 |
| [eCommerce-Skills](https://api.github.com/repos/nexscope-ai/eCommerce-Skills) | 1,260 | 2026-08-26 | MIT |
| [email-marketing-bible](https://api.github.com/repos/CosmoBlk/email-marketing-bible) | 354 | 2026-10-13 | MIT |
| [ai-restaurant-claude](https://api.github.com/repos/zubair-trabzada/ai-restaurant-claude) | 34 | 2026-05-20 | MIT |
| [restaurant-claude-skills](https://api.github.com/repos/miron-tech/restaurant-claude-skills) | 2 | 2026-10-08 | MIT |
| [content-skills](https://api.github.com/repos/vstorm-co/content-skills) | 26 | 2026-04-16 | MIT |
| [xhs-note-creator](https://api.github.com/repos/LinkRogers/xhs-note-creator) | 8 | 2026-02-12 | README称MIT，API未识别 |
| [restaurant-retail-content-flow](https://api.github.com/repos/seedream0311-ai/restaurant-retail-content-flow) | 0 | 2026-09-10 | 未见LICENSE |
| [douyin-local-ops-skill](https://api.github.com/repos/xinyuxinsheng/douyin-local-ops-skill) | 3 | 2026-08-20 | 未见LICENSE |

skills.sh当前页面另列：ad-creative约134.1K安装、copywriting约235.3K、baoyu-xhs-images约31.4K。这些是目录网站的计数，不代表独立用户、内容质量或商业效果；没有统一核验其他候选的安装量。[ad-creative](https://skills.sh/coreyhaines31/marketingskills/ad-creative)、[copywriting](https://skills.sh/coreyhaines31/marketingskills/copywriting)、[baoyu-xhs-images](https://skills.sh/jimliu/baoyu-skills/baoyu-xhs-images)

如需手动试用，目录页面提供以下选择单项的安装示例；本次未执行：

```powershell
npx skills add https://github.com/coreyhaines31/marketingskills --skill ad-creative
npx skills add https://github.com/coreyhaines31/marketingskills --skill copywriting
npx skills add https://github.com/jimliu/baoyu-skills --skill baoyu-xhs-images
```

本次未安装、运行、连接品牌账号或发送发布；成图质量、中文评分、Windows链路和真实营销效果仍需用品牌资料验证。
