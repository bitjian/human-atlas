# Wikidata 权威中文译名 — 人工仲裁清单

> 📌 带**倾向建议与依据**的版本见 [`wikidata-zh-suggestions.md`](./wikidata-zh-suggestions.md)，
> 由 `python3 scripts/suggest-wikidata-arbitration.py --md docs/wikidata-zh-suggestions.md` 生成。
> 本文件是同一批冲突的**纯数据**版本。

生成方式：`scripts/translate-anatomy-zh.py`（策略 `ATLAS_WIKI_MODE=arbitrate`，默认）。

- 数据源：Wikidata 属性 P1402（= FMA 编号），许可证 CC0
- 裁决方式：把选定的译名写入 `app/i18n/anatomy-zh.ts`（手写词条优先级最高）
- 强制旧行为（无条件覆盖）：`ATLAS_WIKI_MODE=override python3 scripts/translate-anatomy-zh.py`

## 统计

| 指标 | 数值 |
| --- | --- |
| Wikidata 中文标签命中 | 615 |
| ① 与规则译名一致（直接采用，无风险） | 261 |
| ② 规则放弃 → 采用权威译名（纯增量） | 16 |
| ③ **与规则译名冲突（需人工裁决）** | **229** |
| ├ 同字换序（命名约定冲突） | 52 |
| └ 其他语义差异（含错概念/加词/缺词） | 177 |

> ③ 冲突项当前**保留规则译名**，未采用 Wikidata，以免引入错概念。

## A. 同字换序（52 条）——两套命名约定正面冲突，必须逐条裁决

| FMA | 英文名 | 规则译名（当前生效） | Wikidata |
| --- | --- | --- | --- |
| FMA3947 | internal carotid artery | 颈内动脉 | 内颈动脉 |
| FMA10646 | superior epigastric artery | 腹壁上动脉 | 上腹壁动脉 |
| FMA10659 | deep cervical artery | 颈深动脉 | 深颈动脉 |
| FMA10662 | inferior thyroid artery | 甲状腺下动脉 | 下甲状腺动脉 |
| FMA14750 | inferior mesenteric artery | 肠系膜下动脉 | 下肠系膜动脉 |
| FMA14754 | middle suprarenal artery | 肾上腺中动脉 | 中肾上腺动脉 |
| FMA14768 | left gastric artery | 胃左动脉 | 左胃动脉 |
| FMA14772 | hepatic artery proper | 肝固有动脉 | 固有肝动脉 |
| FMA14776 | right gastric artery | 胃右动脉 | 右胃动脉 |
| FMA14787 | dorsal pancreatic artery | 胰背侧动脉 | 背侧胰动脉 |
| FMA14792 | great pancreatic artery | 胰大动脉 | 大胰动脉 |
| FMA14796 | left gastro-epiploic artery | 胃网膜左动脉 | 左胃网膜动脉 |
| FMA14832 | superior rectal artery | 直肠上动脉 | 上直肠动脉 |
| FMA15391 | inferior mesenteric vein | 肠系膜下静脉 | 下肠系膜静脉 |
| FMA15394 | left colic vein | 左结肠静脉 | 结肠左静脉 |
| FMA20686 | inferior epigastric artery | 腹壁下动脉 | 下腹壁动脉 |
| FMA20734 | superficial epigastric artery | 腹壁浅动脉 | 浅腹壁动脉 |
| FMA20798 | lateral circumflex femoral artery | 股外侧旋动脉 | 外侧旋股动脉 |
| FMA21162 | inferior epigastric vein | 腹壁下静脉 | 下腹壁静脉 |
| FMA21930 | external anal sphincter | 肛门外括约肌 | 外肛门括约肌 |
| FMA22677 | subscapular artery | 肩胛下动脉 | 下肩胛动脉 |
| FMA22680 | anterior circumflex humeral artery | 肱前旋动脉 | 旋肱前动脉 |
| FMA22684 | posterior circumflex humeral artery | 肱后旋动脉 | 旋肱后动脉 |
| FMA22810 | anterior interosseous artery | 骨间前动脉 | 前骨间动脉 |
| FMA23179 | circumflex scapular artery | 肩胛旋动脉 | 旋肩胛动脉 |
| FMA32519 | levator scapulae | 肩胛提肌 | 提肩胛肌 |
| FMA32525 | rectus capitis posterior major | 后大头直肌 | 头后大直肌 |
| FMA37379 | opponens pollicis | 拇对掌肌 | 对掌拇肌 |
| FMA38503 | extensor digiti minimi | 指小伸肌 | 伸小指肌 |
| FMA38518 | extensor pollicis brevis | 拇短伸肌 | 伸拇短肌 |
| FMA38521 | extensor pollicis longus | 拇长伸肌 | 伸拇长肌 |
| FMA44318 | superficial epigastric vein | 腹壁浅静脉 | 浅腹壁静脉 |
| FMA46312 | rectus capitis anterior | 前头直肌 | 头前直肌 |
| FMA46621 | superior pharyngeal constrictor | 咽上缩肌 | 上咽缩肌 |
| FMA46622 | middle pharyngeal constrictor | 咽中缩肌 | 中咽缩肌 |
| FMA46623 | inferior pharyngeal constrictor | 咽下缩肌 | 下咽缩肌 |
| FMA46727 | levator veli palatini | 帆腭提肌 | 腭帆提肌 |
| FMA50028 | anterior cerebral artery | 大脑前动脉 | 前大脑动脉 |
| FMA50087 | anterior choroidal artery | 脉络丛前动脉 | 前脉络丛动脉 |
| FMA51141 | extensor hallucis brevis | 拇短伸肌 | 伸拇短肌 |
| FMA52642 | supratrochlear nerve | 滑车上神经 | 上滑车神经 |
| FMA52655 | supra-orbital nerve | 眶上神经 | 上眶神经 |
| FMA52675 | anterior ethmoidal nerve | 筛前神经 | 前筛神经 |
| FMA52691 | long ciliary nerve | 睫长神经 | 长睫神经 |
| FMA52693 | infratrochlear nerve | 滑车下神经 | 下滑车神经 |
| FMA54736 | inferior nasal concha | 鼻下甲 | 下鼻甲 |
| FMA61834 | putamen | 壳核 | 核壳 |
| FMA61835 | globus pallidus | 球苍白 | 苍白球 |
| FMA61907 | inferior temporal gyrus | 颞下回 | 下颞回 |
| FMA61918 | parahippocampal gyrus | 海马旁回 | 旁海马回 |
| FMA67943 | pons | 脑桥 | 桥脑 |
| FMA69264 | inferior suprarenal artery | 肾上腺下动脉 | 下肾上腺动脉 |

## B. 其他语义差异（177 条）——含错概念、加词、缺词

| FMA | 英文名 | 规则译名（当前生效） | Wikidata |
| --- | --- | --- | --- |
| FMA3895 | circumflex branch of left coronary artery | 左冠状动脉旋支 | 左回旋支动脉 |
| FMA3932 | brachiocephalic artery | 头臂动脉 | 头臂动脉干 |
| FMA3960 | internal thoracic artery | 胸内动脉 | 乳内动脉 |
| FMA3990 | thyrocervical trunk | 甲状颈干 | 甲状腺颈动脉干 |
| FMA4707 | great cardiac vein | 心大静脉 | 心脏大静脉 |
| FMA4713 | middle cardiac vein | 心中静脉 | 心脏中静脉 |
| FMA4714 | small cardiac vein | 心小静脉 | 心脏小静脉 |
| FMA4729 | internal thoracic vein | 胸内静脉 | 胸廓内静脉 |
| FMA5889 | autonomic ganglion | 自主神经节 | 自律神经节 |
| FMA5894 | parasympathetic ganglion | 副交感神经节 | 副交感神经节（parasympathetic ganglion） |
| FMA6964 | ciliary ganglion | 睫神经节 | 睫状神经节 |
| FMA9621 | muscle of upper limb | 上肢肌 | 上肢肌肉 |
| FMA9622 | muscle of lower limb | 下肢肌 | 下肢肌肉 |
| FMA9629 | supraspinatus | 冈上肌 | 棘上肌 |
| FMA9637 | portion of tissue | 组织 | 生物组织 |
| FMA9703 | nasolacrimal duct | 鼻泪管 | 泪器 |
| FMA10636 | costocervical trunk | 肋颈干 | 肋颈动脉干 |
| FMA11336 | linea alba | 白线 | 腹部白线 |
| FMA12823 | incisor tooth | 切牙 | 门齿 |
| FMA13344 | thyrohyoid | 甲状舌骨 | 甲状舌骨肌 |
| FMA13379 | rhomboid major | 大菱形肌 | 大菱肌 |
| FMA13380 | rhomboid minor | 小菱形肌 | 小菱肌 |
| FMA14333 | common iliac vein | 髂总静脉 | 肠骨的静脉 |
| FMA14344 | testicular vein | 睾丸静脉 | 精索静脉 |
| FMA14348 | suprarenal vein | 肾上腺静脉 | 右肾上腺静脉 |
| FMA14734 | inferior phrenic artery | 膈下动脉 | 横膈下动脉 |
| FMA19090 | pubococcygeus | 耻尾肌 | 耻骨尾骨肌 |
| FMA19617 | corpus spongiosum of penis | 阴茎尿道海绵体 | 尿道海绵体 |
| FMA19795 | dorsal artery of penis | 阴茎背侧动脉 | 阴茎背动脉 |
| FMA22298 | obturator internus | 闭孔内 | 闭孔内肌 |
| FMA22299 | obturator externus | 闭孔外 | 外闭孔肌 |
| FMA22431 | vastus lateralis | 股外侧肌 | 外侧广肌 |
| FMA22441 | adductor longus | 长收肌 | 内收长肌 |
| FMA22442 | adductor brevis | 短收肌 | 内收短肌 |
| FMA22443 | adductor magnus | 大收肌 | 内收大肌 |
| FMA22474 | muscle of posterior compartment of leg | 小腿后区室肌 | 小腿肚 |
| FMA22533 | extensor hallucis longus | 拇长伸肌 | 伸足拇长肌 |
| FMA22534 | extensor digitorum longus | 趾长伸肌 | 伸足趾长肌 |
| FMA22593 | flexor hallucis longus | 拇长屈肌 | 足部屈肌 |
| FMA22674 | lateral thoracic artery | 胸外侧动脉 | 外胸动脉 |
| FMA22695 | deep brachial artery | 肱深动脉 | 臂深动脉 |
| FMA22748 | radial recurrent artery | 桡返动脉 | 桡侧返动脉 |
| FMA22828 | semispinalis thoracis | 胸半棘肌 | 背半棘肌 |
| FMA22834 | superficial palmar arterial arch | 掌侧动脉浅弓 | 浅掌枝 |
| FMA22838 | deep palmar arterial arch | 掌侧动脉深弓 | 深掌弓 |
| FMA22914 | superficial palmar venous arch | 掌侧静脉浅弓 | 浅掌静脉弓 |
| FMA23709 | scaphoid | 舟骨 | 手舟骨 |
| FMA30320 | duct | 管 | 导管 |
| FMA32526 | rectus capitis posterior minor | 后小头直肌 | 小后头直筋 |
| FMA32527 | obliquus capitis superior | 头后上斜肌 | 头上斜肌 |
| FMA32528 | obliquus capitis inferior | 头后下斜肌 | 头下斜肌 |
| FMA32546 | infraspinatus | 冈下肌 | 棘下肌 |
| FMA37382 | abductor digiti minimi of hand | 手指小展肌 | 外展小指肌 |
| FMA37383 | flexor digiti minimi brevis of hand | 手指小短屈肌 | 屈小指短肌 |
| FMA37384 | opponens digiti minimi of hand | 手指小对掌肌 | 小指对掌肌 |
| FMA37448 | abductor hallucis | 拇展肌 | 𧿹外展肌 |
| FMA37450 | flexor digitorum brevis | 趾短屈肌 | 伸趾短肌 |
| FMA37451 | abductor digiti minimi of foot | 足指小展肌 | 小趾展肌 |
| FMA37452 | flexor accessorius | 副屈肌 | 跖方肌 |
| FMA37453 | lumbrical of foot | 足蚓状肌 | 蚓状肌 |
| FMA37455 | flexor digiti minimi brevis of foot | 足指小短屈肌 | 屈小趾短肌 |
| FMA37458 | plantar interosseous of foot | 足底骨间肌 | 骨间跖侧肌 |
| FMA37664 | coracobrachialis | 喙肱肌 | 喙突肱肌 |
| FMA38453 | pronator quadratus | 旋前肌方肌 | 旋前方肌 |
| FMA38459 | flexor carpi radialis | 桡腕屈肌 | 桡侧屈腕肌 |
| FMA38494 | extensor carpi radialis longus | 桡腕长伸肌 | 桡侧伸腕长肌 |
| FMA38497 | extensor carpi radialis brevis | 桡腕短伸肌 | 桡侧伸腕短肌 |
| FMA38506 | extensor carpi ulnaris | 尺腕伸肌 | 尺侧伸腕肌 |
| FMA38515 | abductor pollicis longus | 拇长展肌 | 外展拇长肌 |
| FMA38524 | extensor indicis | 示指伸肌 | 伸食指肌 |
| FMA39988 | flexor retinaculum of wrist | 腕支持带屈肌 | 手屈肌支持带 |
| FMA43885 | adductor minimus | 最小收肌 | 内收小肌 |
| FMA43915 | dorsalis pedis artery | 背侧足动脉 | 足背动脉 |
| FMA43926 | lateral plantar artery | 足底外侧动脉 | 外跖动脉 |
| FMA43942 | plantar arch | 足底弓 | 掌动脉弓 |
| FMA44248 | long plantar ligament | 足底长韧带 | 长跖韧带 |
| FMA44332 | posterior tibial vein | 胫后静脉 | 胫骨后静脉 |
| FMA45728 | anatomical lobe | 解剖叶 | 乳叶 |
| FMA45732 | parenchyma | 实质 | 薄壁组织 |
| FMA46291 | digastric | 二腹肌 | 二腹肌前腹 |
| FMA46316 | rectus capitis lateralis | 外侧头直肌 | 头侧直肌 |
| FMA46320 | mylohyoid | 下颌舌骨肌 | 颏舌肌 |
| FMA46579 | lateral crico-arytenoid | 外侧环杓肌 | 外环杓肌 |
| FMA46582 | transverse arytenoid | 杓横肌 | 杓肌 |
| FMA46664 | stylopharyngeus | 茎突咽肌 | 茎咽肌 |
| FMA46665 | salpingopharyngeus | 咽鼓管咽肌 | 耳咽管咽肌 |
| FMA46730 | tensor veli palatini | 帆腭张肌 | 颚帆张肌 |
| FMA49037 | medial rectus | 内侧直肌 | 内直肌 |
| FMA49038 | lateral rectus | 外侧直肌 | 眼直肌 |
| FMA49039 | superior oblique | 上斜肌 | 眼斜肌 |
| FMA51041 | deep femoral vein | 股深静脉 | 股骨深静脉 |
| FMA51099 | tibialis posterior | 胫骨后肌 | 胫后肌 |
| FMA52781 | external ear | 外耳 | 动耳肌 |
| FMA53667 | hair | 毛 | 毛发 |
| FMA54237 | eyebrow | 眉 | 眉毛 |
| FMA54319 | pubic hair | 耻骨毛 | 阴毛 |
| FMA55077 | pharyngeal raphe | 咽缝 | 咽裂 |
| FMA55093 | submandibular gland | 下颌下腺 | 下颌腺 |
| FMA55111 | cuneiform cartilage | 楔状软骨 | 楔形软骨 |
| FMA55227 | hyo-epiglottic ligament | 舌会厌韧带 | 舌骨会厌韧带 |
| FMA55230 | thyro-epiglottic ligament | 甲会厌韧带 | 甲状会厌韧带 |
| FMA55618 | pterygomandibular raphe | 翼下颌缝 | 翼下颔缝 |
| FMA55636 | canine tooth | 尖牙 | 犬齿 |
| FMA55637 | premolar tooth | 前磨牙 | 前臼齿 |
| FMA55638 | molar tooth | 磨牙 | 大臼齿 |
| FMA55801 | upper first secondary premolar tooth | 第一上次级前磨牙 | 上颌第一前臼齿 |
| FMA55802 | upper second secondary premolar tooth | 第二上次级前磨牙 | 上颌第二前臼齿 |
| FMA55803 | lower first secondary premolar tooth | 第一下次级前磨牙 | 下颌第一前臼齿 |
| FMA55804 | lower second secondary premolar tooth | 第二下次级前磨牙 | 下颌第二前臼齿 |
| FMA58078 | anterior chamber of eyeball | 眼球前腔 | 前房 |
| FMA58102 | fibrous layer of eyeball | 眼球纤维层 | 眼球纤维膜 |
| FMA58838 | suspensory ligament of lens | 晶状体悬韧带 | 睫状韧带 |
| FMA59086 | tarsal plate of eyelid | 眼睑跗骨板 | 睑板 |
| FMA59503 | septal nasal cartilage | 鼻隔软骨 | 鼻中隔软骨 |
| FMA59504 | major alar cartilage | 大翼软骨 | 鼻翼大软骨 |
| FMA59511 | lateral nasal cartilage | 鼻外侧软骨 | 鼻外软骨 |
| FMA59816 | lip | 唇 | 唇结节 |
| FMA61860 | inferior frontal gyrus | 额下回 | 额叶额下回 |
| FMA61934 | choroid plexus of cerebral hemisphere | 大脑半球脉络膜丛 | 脉络丛 |
| FMA61965 | fornix of forebrain | 前脑穹窿 | 脑穹窿 |
| FMA61974 | stria terminalis | 终纹 | 终纹床核 |
| FMA62080 | stria medullaris of thalamus | 丘脑纹髓 | 髓纹 |
| FMA62209 | lateral geniculate body | 外侧膝状体 | 外侧膝状核 |
| FMA62211 | medial geniculate body | 内侧膝状体 | 内膝状核 |
| FMA62434 | cingulate gyrus | 扣带回 | 扣带皮层 |
| FMA67242 | gray matter of neuraxis | 神经轴灰质 | 灰质 |
| FMA67977 | dorsal venous network of hand | 手静脉背侧网 | 手背静脉 |
| FMA68068 | inferior phrenic vein | 膈下静脉 | 横膈下静脉 |
| FMA70800 | set of dorsal metacarpal arteries | 背侧掌骨动脉组 | 掌背动脉 |
| FMA70922 | set of perforating veins | 穿静脉组 | 穿支静脉 |
| FMA74877 | mammillary body | 乳头体 | 乳头状体 |
| FMA77179 | spinalis | 棘肌 | 脊柱胸肌 |
| FMA78497 | central canal of spinal cord | 脊髓中央管 | 中央管 |
| FMA83686 | nucleus of neuraxis | 神经轴核 | 核团 |
| FMA83874 | gyrus of neuraxis | 神经轴回 | 脑回 |
| FMA83929 | white matter of neuraxis | 神经轴白质 | 白质 |
| FMA83966 | tentorium cerebelli | 小脑幕 | 小脑疝 |
| FMA3862 | anterior interventricular branch of left coronary artery | 左冠状动脉前室间支 | 前室间动脉 |
| FMA7152 | alimentary system | 消化系统 | 排遗系统 |
| FMA7154 | head | 头 | 头部 |
| FMA7160 | genital system | 生殖系统 | 人类生殖系统 |
| FMA7184 | lower limb | 下肢 | 人类腿部 |
| FMA7480 | rib cage | 肋廓 | 胸廓 |
| FMA7482 | musculoskeletal system | 肌骨骼系统 | 人体肌肉骨骼系统 |
| FMA9496 | fibrous skeleton of heart | 心脏纤维骨骼 | 心纤维环 |
| FMA9576 | thorax | 胸 | 胸部 |
| FMA9578 | pelvis | 骨盆 | 人类骨盆 |
| FMA9826 | mediastinum | 纵隔 | 纵隔膜 |
| FMA10428 | thoracic wall | 胸壁 | 胸腔壁 |
| FMA10429 | wall of abdomen proper | 腹固有壁 | 腹壁 |
| FMA11343 | right foot | 右足 | 右脚 |
| FMA11344 | left foot | 左足 | 左脚 |
| FMA16580 | bony pelvis | 骨性骨盆 | 髋骨 |
| FMA20394 | human body | 人体 | 人体解剖 |
| FMA23881 | skeletal system | 骨骼系统 | 人体骨架 |
| FMA24728 | face | 面 | 脸 |
| FMA24980 | right leg | 右小腿 | 右腿 |
| FMA46472 | nose | 鼻 | 人类鼻子 |
| FMA49184 | mouth | 口 | 口腔 |
| FMA50040 | left coronary artery | 左冠状动脉 | 左冠状动脉血管 |
| FMA50454 | cerebral arterial circle | 大脑动脉环 | Willis环 |
| FMA55675 | neuraxis | 神经轴 | 中枢神经系统 |
| FMA60325 | right thumb | 右拇指 | 右手拇指 |
| FMA60326 | left thumb | 左拇指 | 左手拇指 |
| FMA60327 | right little finger | 右小指 | 右手小指 |
| FMA60328 | left little finger | 左小指 | 左手小指 |
| FMA60329 | right ring finger | 右环指 | 右手无名指 |
| FMA60330 | left ring finger | 左环指 | 左手无名指 |
| FMA60331 | right middle finger | 右中指 | 右手中指 |
| FMA60332 | left middle finger | 左中指 | 左手中指 |
| FMA60333 | right index finger | 右示指 | 右手食指 |
| FMA60334 | left index finger | 左示指 | 左手食指 |
| FMA61681 | back of abdomen | 腹背 | 腰部 |
| FMA62000 | telencephalon | 端脑 | 大脑 |
| FMA72979 | integumentary system | 皮肤系统 | 表皮系统 |
| FMA74657 | integument | 体被 | 覆盖物 |
| FMA242787 | ventricular system of brain | 脑室系统 | 脑室 |
