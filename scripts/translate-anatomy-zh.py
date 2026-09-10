# -*- coding: utf-8 -*-
"""按解剖学词表规则批量生成中文术语映射表。

用法：
  python3 scripts/translate-anatomy-zh.py                 # 重新生成 app/i18n/terms-zh.ts
  python3 scripts/translate-anatomy-zh.py "left rib" ...  # 调试单个术语的分词与译文

改进译名：编辑 scripts/anatomy_lexicon.py 词表后重新运行；个别词条可直接在
app/i18n/anatomy-zh.ts 里追加同 ID 覆盖（手写优先）。"""
import json, os, re, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anatomy_lexicon import W

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 部位形容词（中文语序上要提到方位词之前：anterior tibial artery -> 胫前动脉）
LOC = set("""tibial femoral brachial radial ulnar axillary carotid renal hepatic gastric splenic pancreatic
pulmonary cardiac coronary aortic frontal temporal parietal occipital ethmoidal lacrimal maxillary mandibular
zygomatic mastoid styloid cervical thoracic lumbar sacral coccygeal iliac gluteal popliteal fibular peroneal
humeral scapular clavicular sternal costal nasal orbital plantar palmar cerebral cerebellar pontine thalamic
hypothalamic cortical medullary bronchial tracheal esophageal oesophageal duodenal jejunal ileal colic cecal
caecal lingual buccal labial dental gingival palatal pharyngeal laryngeal tonsillar vestibular cochlear adrenal
thyroid thymic mammary uterine prostatic testicular peritoneal mesenteric omental intercostal
interosseous intervertebral interlobar interlobular nuchal subcutaneous cutaneous muscular venous arterial spinal
biliary callosal lingular jugular rectal appendicular gluteal sacral""".split())

# 这些"部位+结构"短语会挡住方位词插入（deep femoral vein 应作 股深静脉），拆开按词处理
DROP = {p.strip() for p in """femoral vein,renal vein,hepatic vein,splenic vein,iliac vein,vertebral vein,
gastric vein,mesenteric vein,oesophageal vein,subclavian vein,jugular vein,pulmonary vein,femoral artery,
popliteal artery,brachial artery,radial artery,ulnar artery,renal artery,gastric artery,hepatic artery,
splenic artery,iliac artery,subclavian artery,vertebral artery,pulmonary artery,renal pelvis,renal cortex,
renal medulla,pancreatic duct,hepatic duct,pulmonary trunk""".replace('\n', '').split(',')}

# 序数词在中文里紧跟方位词之后、部位词之前：second posterior intercostal artery -> 第二肋间后动脉
ORD = {'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth',
       'eleventh', 'twelfth'}
SIDE = {'left', 'right', 'bilateral'}

EXTRA = {
'toe': ('足趾', 'n'), 'toes': ('足趾', 'n'), 'finger': ('指', 'n'), 'fingers': ('指', 'n'),
'thumb': ('拇指', 'n'), 'great toe': ('拇趾', 'n'), 'little toe': ('小趾', 'n'),
'xiphoid': ('剑突', 'n'), 'colliculus': ('丘', 'n'), 'colliculi': ('丘', 'n'),
'tensor': ('张肌', 'm'), 'fascia lata': ('阔筋膜', 'n'), 'latae': ('阔', 'mod'), 'fasciae': ('筋膜', 'n'),
'perforating': ('穿', 'mod'), 'perforatus': ('穿', 'mod'), 'perforata': ('穿', 'mod'),
'pericallosal': ('胼胝体周', 'mod'), 'transversalis': ('横', 'mod'),
'lingular': ('舌叶', 'loc'), 'lingula': ('小舌', 'n'), 'mylohyoid': ('下颌舌骨肌', 'm'),
'triquetral': ('三角骨', 'n'), 'crico-arytenoid': ('环杓', 'n'), 'cricoarytenoid': ('环杓', 'n'),
'pectoralis': ('胸肌', 'm'), 'biliary': ('胆', 'n'), 'canine': ('尖', 'mod'), 'premolar': ('前磨', 'mod'),
'molar': ('磨', 'mod'), 'incisor': ('切', 'mod'), 'costal': ('肋', 'loc'),
'lake': ('湖', 'n'), 'cavernous': ('海绵体', 'n'), 'taenia': ('带', 'n'), 'omentalis': ('大网膜', 'n'),
'radialis': ('桡', 'loc'), 'ulnaris': ('尺', 'loc'), 'medialis': ('内侧', 'mod'), 'lateralis': ('外侧', 'mod'),
'anterioris': ('前', 'mod'), 'posterioris': ('后', 'mod'), 'superioris': ('上', 'mod'), 'inferioris': ('下', 'mod'),
'nasalis': ('鼻', 'loc'), 'orbicularis': ('轮匝肌', 'm'), 'mentalis': ('颏肌', 'm'),
'zygomaticus': ('颧肌', 'm'), 'frontalis': ('额肌', 'm'), 'occipitalis': ('枕肌', 'm'),
'stapedius': ('镫骨肌', 'm'), 'sphincter': ('括约肌', 'm'), 'dilator': ('开肌', 'm'),
'constrictor': ('缩肌', 'm'), 'vocalis': ('声带肌', 'm'), 'arytenoid': ('杓状软骨', 'n'),
'cricoid': ('环状软骨', 'n'), 'epiglottic': ('会厌', 'loc'), 'epiglottis': ('会厌', 'n'),
'thyrohyoid': ('甲状舌骨', 'loc'), 'sternohyoid': ('胸骨舌骨肌', 'm'), 'omohyoid': ('肩胛舌骨肌', 'm'),
'sternothyroid': ('胸骨甲状肌', 'm'), 'digastric': ('二腹肌', 'm'), 'stylohyoid': ('茎突舌骨肌', 'm'),
'geniohyoid': ('颏舌骨肌', 'm'), 'genioglossus': ('颏舌肌', 'm'), 'hyoglossus': ('舌骨舌肌', 'm'),
'styloglossus': ('茎突舌肌', 'm'), 'palatoglossus': ('腭舌肌', 'm'),
'longus colli': ('颈长肌', 'm'), 'longus capitis': ('头长肌', 'm'), 'rectus capitis': ('头直肌', 'm'),
'rectus abdominis': ('腹直肌', 'm'), 'rectus femoris': ('股直肌', 'm'), 'vastus': ('股肌', 'm'),
'scalenus': ('斜角肌', 'm'), 'obliquus capitis': ('头斜肌', 'm'), 'pulmonary trunk': ('肺动脉干', 'n'),
'bronchial tree': ('支气管树', 'n'), 'segmental bronchus': ('段支气管', 'n'),
'hepatic vein': ('肝静脉', 'n'), 'portal vein': ('门静脉', 'n'), 'splenic vein': ('脾静脉', 'n'),
'renal vein': ('肾静脉', 'n'), 'iliac vein': ('髂静脉', 'n'), 'vertebral vein': ('椎静脉', 'n'),
'basilic vein': ('贵要静脉', 'n'), 'cephalic vein': ('头静脉', 'n'), 'saphenous vein': ('隐静脉', 'n'),
'great saphenous vein': ('大隐静脉', 'n'), 'small saphenous vein': ('小隐静脉', 'n'),
'mesenteric vein': ('肠系膜静脉', 'n'), 'gastric vein': ('胃静脉', 'n'), 'oesophageal vein': ('食管静脉', 'n'),
'gingiva': ('牙龈', 'n'), 'palate': ('腭', 'n'), 'uvula': ('悬雍垂', 'n'), 'frenulum': ('系带', 'n'),
'papilla': ('乳头', 'n'), 'cusp': ('瓣尖', 'n'), 'commissure': ('连合', 'n'), 'vallecula': ('谷', 'n'),
'aortic arch': ('主动脉弓', 'n'), 'aortic valve': ('主动脉瓣', 'n'), 'aortic sinus': ('主动脉窦', 'n'),
'tunica': ('膜', 'n'), 'adventitia': ('外膜', 'n'), 'intima': ('内膜', 'n'), 'media': ('中膜', 'n'),
# 拉丁肌名固定搭配（标准中文译名）
'transverse arytenoid': ('杓横肌', 'm'), 'oblique arytenoid': ('杓斜肌', 'm'),
'obliquus capitis superior': ('头后上斜肌', 'm'), 'obliquus capitis inferior': ('头后下斜肌', 'm'),
'tibialis anterior': ('胫骨前肌', 'm'), 'tibialis posterior': ('胫骨后肌', 'm'),
'fibularis longus': ('腓骨长肌', 'm'), 'fibularis brevis': ('腓骨短肌', 'm'),
'peroneus longus': ('腓骨长肌', 'm'), 'peroneus brevis': ('腓骨短肌', 'm'),
'extensor digitorum longus': ('趾长伸肌', 'm'), 'extensor hallucis longus': ('拇长伸肌', 'm'),
'extensor digitorum brevis': ('趾短伸肌', 'm'), 'extensor hallucis brevis': ('拇短伸肌', 'm'),
'flexor digitorum longus': ('趾长屈肌', 'm'), 'flexor hallucis longus': ('拇长屈肌', 'm'),
'flexor digitorum brevis': ('趾短屈肌', 'm'), 'flexor hallucis brevis': ('拇短屈肌', 'm'),
'adductor longus': ('长收肌', 'm'), 'adductor magnus': ('大收肌', 'm'), 'adductor brevis': ('短收肌', 'm'),
'pectoralis major': ('胸大肌', 'm'), 'pectoralis minor': ('胸小肌', 'm'),
'gluteus maximus': ('臀大肌', 'm'), 'gluteus medius': ('臀中肌', 'm'), 'gluteus minimus': ('臀小肌', 'm'),
'teres major': ('大圆肌', 'm'), 'teres minor': ('小圆肌', 'm'),
'rhomboideus major': ('大菱形肌', 'm'), 'rhomboid major': ('大菱形肌', 'm'), 'rhomboid minor': ('小菱形肌', 'm'),
'serratus anterior': ('前锯肌', 'm'), 'serratus posterior superior': ('上后锯肌', 'm'),
'serratus posterior inferior': ('下后锯肌', 'm'), 'erector spinae': ('竖脊肌', 'm'),
'levator scapulae': ('肩胛提肌', 'm'), 'levator palpebrae superioris': ('上睑提肌', 'm'),
'orbicularis oculi': ('眼轮匝肌', 'm'), 'orbicularis oris': ('口轮匝肌', 'm'),
'latissimus dorsi': ('背阔肌', 'm'), 'quadratus lumborum': ('腰方肌', 'm'),
'transversus abdominis': ('腹横肌', 'm'), 'obliquus externus abdominis': ('腹外斜肌', 'm'),
'obliquus internus abdominis': ('腹内斜肌', 'm'), 'biceps brachii': ('肱二头肌', 'm'),
'triceps brachii': ('肱三头肌', 'm'), 'quadriceps femoris': ('股四头肌', 'm'),
'tensor fasciae latae': ('阔筋膜张肌', 'm'), 'levator ani': ('肛提肌', 'm'),
'puborectalis': ('耻骨直肠肌', 'm'), 'bulbospongiosus': ('球海绵体肌', 'm'),
'ischiocavernosus': ('坐骨海绵体肌', 'm'), 'sphincter ani': ('肛门括约肌', 'm'),
'cricothyroid': ('环甲肌', 'm'), 'straight': ('直', 'mod'), 'anal canal': ('肛管', 'n'),
'sigmoid': ('乙状', 'mod'), 'ileocaecal': ('回盲', 'mod'), 'ileocecal': ('回盲', 'mod'),
'thyroid cartilage': ('甲状软骨', 'n'), 'cricoid cartilage': ('环状软骨', 'n'),
'arytenoid cartilage': ('杓状软骨', 'n'), 'corniculate cartilage': ('小角软骨', 'n'),
'cuneiform cartilage': ('楔状软骨', 'n'), 'epiglottic cartilage': ('会厌软骨', 'n'),
'vermiform': ('蚓状', 'mod'), 'ampulla': ('壶腹', 'n'), 'crus': ('脚', 'n'), 'crura': ('脚', 'n'),
'cornu': ('角', 'n'), 'atlas': ('寰椎', 'n'), 'axis': ('枢椎', 'n'), 'carpus': ('腕', 'n'),
'tarsus': ('跗', 'n'), 'metatarsus': ('跖', 'n'), 'metacarpus': ('掌', 'n'),
'superior oblique': ('上斜肌', 'm'), 'inferior oblique': ('下斜肌', 'm'),
'external oblique': ('外斜肌', 'm'), 'internal oblique': ('内斜肌', 'm'),
'crico-arytenoid': ('环杓肌', 'm'), 'arytenoideus': ('杓肌', 'm'),
'hallux': ('拇趾', 'n'), 'pollex': ('拇指', 'n'), 'clavicula': ('锁骨', 'n'),
'venae': ('静脉', 'n'), 'arteriae': ('动脉', 'n'), 'ramus': ('支', 'n'), 'rami': ('支', 'n'),
# 第三轮：按未识别词频补充
'digital': ('指', 'loc'), 'foot': ('足', 'n'), 'feet': ('足', 'n'), 'hand': ('手', 'n'),
'circumflex': ('旋', 'mod'), 'descending': ('降', 'mod'), 'ascending': ('升', 'mod'),
'genicular': ('膝', 'loc'), 'phrenic': ('膈', 'loc'), 'epigastric': ('腹壁', 'loc'),
'recurrent': ('返', 'mod'), 'collateral': ('侧副', 'mod'), 'callosomarginal': ('胼胝体缘', 'mod'),
'minimi': ('小', 'mod'), 'long': ('长', 'mod'), 'short': ('短', 'mod'), 'big': ('大', 'mod'),
'symphysis': ('联合', 'n'), 'thoraco-acromial': ('胸肩峰', 'mod'), 'neuraxis': ('神经轴', 'n'),
'bronchopulmonary': ('支气管肺', 'mod'), 'choroidal': ('脉络丛', 'loc'), 'choroid': ('脉络膜', 'n'),
'communicating': ('交通', 'mod'), 'nose': ('鼻', 'n'), 'hemisphere': ('半球', 'n'),
'investing': ('被覆', 'mod'), 'eyeball': ('眼球', 'n'), 'forearm': ('前臂', 'n'),
'iliocostalis': ('髂肋肌', 'm'), 'median': ('正中', 'mod'), 'cuneiform': ('楔', 'mod'),
'pancreaticoduodenal': ('胰十二指肠', 'loc'), 'free': ('游离', 'mod'), 'eyelid': ('眼睑', 'n'),
'cervicis': ('颈', 'n'), 'suprarenal': ('肾上腺', 'loc'), 'subsegmental': ('亚段', 'mod'),
'skeleton': ('骨骼', 'n'), 'arteria': ('动脉', 'n'), 'limb': ('肢', 'n'), 'chest': ('胸', 'n'),
'leg': ('小腿', 'n'), 'caudate': ('尾状', 'mod'), 'septal': ('隔', 'mod'), 'side': ('侧', 'n'),
'precentral': ('中央前', 'loc'), 'postcentral': ('中央后', 'loc'), 'frontobasal': ('额底', 'mod'),
'ileocolic': ('回结肠', 'loc'), 'anatomical': ('解剖', 'mod'), 'mediastinum': ('纵隔', 'n'),
'nasociliary': ('鼻睫', 'loc'), 'ophthalmic': ('眼', 'loc'), 'biceps': ('二头肌', 'm'),
'gemellus': ('孖肌', 'm'), 'brachium': ('臂', 'n'), 'stria': ('纹', 'n'),
'subscapular': ('肩胛下', 'loc'), 'thigh': ('大腿', 'n'), 'content': ('内容物', 'n'),
'tendinous': ('腱性', 'mod'), 'lens': ('晶状体', 'n'), 'quadratus': ('方肌', 'm'),
'costarum': ('肋', 'n'), 'acromial': ('肩峰', 'loc'), 'posteromedial': ('后内侧', 'mod'),
'geniculate': ('膝状', 'mod'), 'hepatovenous': ('肝静脉', 'mod'), 'aorta': ('主动脉', 'n'),
'subcostal': ('肋下', 'loc'), 'musculophrenic': ('肌膈', 'loc'), 'marginal': ('缘', 'mod'),
'suprascapular': ('肩胛上', 'loc'), 'thoracodorsal': ('胸背', 'loc'), 'pectoral': ('胸', 'loc'),
'veli': ('帆', 'n'), 'component': ('成分', 'n'), 'systemic': ('体', 'mod'), 'chamber': ('腔', 'n'),
'wrist': ('腕', 'n'), 'paracentral': ('旁中央', 'mod'), 'forebrain': ('前脑', 'n'),
'papillary': ('乳头', 'mod'), 'abdomen': ('腹', 'n'), 'calcaneal': ('跟', 'loc'),
'intertransversarius': ('横突间肌', 'm'), 'anterolateral': ('前外侧', 'mod'),
'fornix': ('穹窿', 'n'), 'costocervical': ('肋颈', 'loc'), 'subclavius': ('锁骨下肌', 'm'),
'transversospinalis': ('横突棘肌', 'm'), 'interspinalis': ('棘间肌', 'm'),
'longissimus': ('最长肌', 'm'), 'subscapularis': ('肩胛下肌', 'm'),
'rotundus': ('圆', 'mod'), 'vastus': ('股肌', 'm'), 'medius': ('中间', 'mod'),
'nervus': ('神经', 'n'), 'musculus': ('肌', 'n'), 'capsular': ('囊', 'mod'),
'radiate': ('辐射', 'mod'), 'acoustic': ('听', 'loc'), 'otic': ('耳', 'loc'),
'labyrinthine': ('迷路', 'loc'), 'spiral': ('螺旋', 'mod'), 'sacral': ('骶', 'loc'),
'femoral': ('股', 'loc'), 'sciatic': ('坐骨', 'loc'), 'glossopharyngeal': ('舌咽', 'loc'),
# 第四轮
'ciliary': ('睫', 'loc'), 'palatini': ('腭', 'n'), 'thyrocervical': ('甲状颈', 'loc'),
'sesamoid': ('籽骨', 'n'), 'brachiocephalic': ('头臂', 'loc'), 'pudendal': ('阴部', 'loc'),
'superficialis': ('浅', 'mod'), 'insular': ('岛', 'loc'), 'splenial': ('压部', 'mod'),
'terminal': ('终', 'mod'), 'terminalis': ('终', 'mod'), 'prefrontal': ('前额', 'loc'),
'midbrain': ('中脑', 'n'), 'telencephalon': ('端脑', 'n'), 'princeps': ('主要', 'mod'),
'conus': ('圆锥', 'n'), 'thyro-arytenoid': ('甲杓肌', 'm'), 'vascular': ('血管', 'mod'),
'sector': ('区', 'n'), 'intrapulmonary': ('肺内', 'mod'), 'intrinsic': ('固有', 'mod'),
'musculature': ('肌群', 'n'), 'jaw': ('颌', 'n'), 'sac': ('囊', 'n'), 'retina': ('视网膜', 'n'),
'coccygeus': ('尾骨肌', 'm'), 'iliococcygeus': ('髂尾肌', 'm'), 'pubococcygeus': ('耻尾肌', 'm'),
'intertransversarii': ('横突间肌', 'm'), 'interspinales': ('棘间肌', 'm'),
'postcommunicating': ('交通后', 'mod'), 'main': ('主', 'mod'), 'ureteric': ('输尿管', 'loc'),
'thorax': ('胸', 'n'), 'pelvis': ('骨盆', 'n'), 'mouth': ('口', 'n'), 'knee': ('膝', 'n'),
'corona': ('冠', 'n'), 'cornea': ('角膜', 'n'), 'infratrochlear': ('滑车下', 'loc'),
'iris': ('虹膜', 'n'), 'canaliculus': ('小管', 'n'), 'nasolacrimal': ('鼻泪', 'loc'),
'sclera': ('巩膜', 'n'), 'suspensory': ('悬', 'mod'), 'supra-orbital': ('眶上', 'loc'),
'supratrochlear': ('滑车上', 'loc'), 'trochlea': ('滑车', 'n'), 'vitreous': ('玻璃体', 'n'),
'accessorius': ('副', 'mod'), 'iliotibial': ('髂胫', 'loc'), 'externus': ('外', 'mod'),
'internus': ('内', 'mod'), 'pectineus': ('耻骨肌', 'm'), 'intermedius': ('中间', 'mod'),
'anal': ('肛门', 'loc'), 'breves': ('短', 'mod'), 'longi': ('长', 'mod'),
'sternocostal': ('胸肋', 'loc'), 'profundus': ('深', 'mod'), 'precuneal': ('楔前', 'loc'),
'thalamogeniculate': ('丘脑膝状体', 'mod'), 'intermediomedial': ('中间内侧', 'mod'),
'polar': ('极', 'mod'), 'thalamoperforating': ('丘脑穿', 'mod'), 'precommunicating': ('交通前', 'mod'),
'vermian': ('蚓部', 'loc'), 'temporo-occipital': ('颞枕', 'loc'), 'amygdala': ('杏仁核', 'n'),
'globus': ('球', 'n'), 'putamen': ('壳核', 'n'), 'medullaris': ('髓', 'mod'),
'dorsalis': ('背侧', 'mod'), 'arcuate': ('弓状', 'mod'), 'network': ('网', 'n'),
'antebrachial': ('前臂', 'loc'), 'cubital': ('肘', 'loc'), 'alar': ('翼', 'mod'),
'palatopharyngeus': ('腭咽肌', 'm'), 'pterygomandibular': ('翼下颌', 'loc'),
'salpingopharyngeus': ('咽鼓管咽肌', 'm'), 'stylopharyngeus': ('茎突咽肌', 'm'),
'sublingual': ('舌下', 'loc'), 'submandibular': ('下颌下', 'loc'),
'aryepiglotticus': ('杓会厌肌', 'm'), 'vocal': ('声', 'mod'), 'corpus': ('体', 'n'),
'vallecula': ('谷', 'n'), 'angle': ('角', 'n'), 'ganglion': ('神经节', 'n'),
'pterygoid': ('翼', 'loc'), 'masseteric': ('咬肌', 'loc'), 'buccinator': ('颊肌', 'm'),
'constrictor': ('缩肌', 'm'), 'digastricus': ('二腹肌', 'm'),
# 第五轮
'raphe': ('缝', 'n'), 'bronchus': ('支气管', 'n'), 'anastomosis': ('吻合', 'n'),
'ciliaris': ('睫', 'mod'), 'pallidus': ('苍白', 'mod'), 'elasticus': ('弹性', 'mod'),
'deferent': ('输精', 'mod'), 'capitate': ('头状骨', 'n'), 'cuboid': ('骰骨', 'n'),
'hamate': ('钩骨', 'n'), 'concha': ('甲', 'n'), 'lunate': ('月骨', 'n'), 'pisiform': ('豌豆骨', 'n'),
'scaphoid': ('舟骨', 'n'), 'trapezium': ('大多角骨', 'n'), 'trapezoid': ('小多角骨', 'n'),
'navicular': ('舟骨', 'n'), 'iliolumbar': ('髂腰', 'loc'), 'shoulder': ('肩', 'n'), 'arm': ('臂', 'n'),
'cluster': ('簇', 'n'), 'tertius': ('第三', 'mod'), 'celiac': ('腹腔', 'loc'),
'hemiazygos': ('半奇', 'mod'), 'hair': ('毛', 'n'), 'mediobasal': ('内侧基底', 'mod'),
'subsuperior': ('亚上', 'mod'), 'laterobasal': ('外侧基底', 'mod'),
'gastroduodenal': ('胃十二指肠', 'loc'), 'gastro-epiploic': ('胃网膜', 'loc'),
'gastroepiploic': ('胃网膜', 'loc'), 'skeletal': ('骨骼', 'mod'), 'postvertebral': ('椎后', 'mod'),
'extrinsic': ('外在', 'mod'), 'cardinal': ('主', 'mod'), 'lobule': ('小叶', 'n'),
'diencephalon': ('间脑', 'n'), 'outflow': ('流出', 'mod'), 'inflow': ('流入', 'mod'),
'eye': ('眼', 'n'), 'innermost': ('最内', 'mod'), 'interpeduncular': ('脚间', 'loc'),
'chiasm': ('交叉', 'n'), 'junction': ('连接', 'n'), 'spongiosum': ('海绵体', 'n'),
'azygos': ('奇', 'mod'), 'variant': ('变异', 'mod'), 'parasympathetic': ('副交感', 'mod'),
'tracheobronchial': ('气管支气管', 'loc'), 'face': ('面', 'n'), 'lobular': ('小叶', 'mod'),
'supramarginal': ('缘上', 'loc'), 'angular': ('角', 'mod'), 'fusiform': ('梭状', 'mod'),
'parahippocampal': ('海马旁', 'loc'), 'cingulate': ('扣带', 'mod'), 'apicoposterior': ('尖后', 'mod'),
'cage': ('廓', 'n'), 'back': ('背', 'n'), 'urinary': ('泌尿', 'mod'), 'gastrointestinal': ('胃肠', 'mod'),
'myocardial': ('心肌', 'loc'), 'linea': ('线', 'n'), 'tentorium': ('幕', 'n'), 'libera': ('游离', 'mod'),
'mesocolica': ('结肠系膜', 'n'), 'uvular': ('腭垂', 'loc'), 'manubrium': ('柄', 'n'),
'mesoappendix': ('阑尾系膜', 'n'), 'mesocolon': ('结肠系膜', 'n'), 'caudal': ('尾侧', 'mod'),
'irregular': ('不规则', 'mod'), 'neural': ('神经', 'mod'), 'visceral': ('内脏', 'mod'),
'pubic': ('耻骨', 'loc'), 'ear': ('耳', 'n'), 'lip': ('唇', 'n'), 'eyebrow': ('眉', 'n'),
'lumbrical': ('蚓状肌', 'm'), 'interventricular': ('室间', 'n'), 'interatrial': ('房间', 'n'),
'palmaris longus': ('掌长肌', 'm'), 'biceps femoris': ('股二头肌', 'm'),
'interosseous membrane': ('骨间膜', 'n'), 'tendinous ring': ('腱环', 'n'),
# 第六轮：补齐 LOC 中缺译名的词 + 其他缺失基础词
'appendicular': ('阑尾', 'loc'), 'callosal': ('胼胝体', 'loc'), 'jugular': ('颈', 'loc'),
'nuchal': ('项', 'loc'), 'rectal': ('直肠', 'loc'),
'small': ('小', 'mod'), 'connective': ('结缔', 'mod'), 'peritoneum': ('腹膜', 'n'),
'parenchyma': ('实质', 'n'), 'decussation': ('交叉', 'n'), 'continuity': ('连续', 'n'),
'conduit': ('管道', 'n'), 'sector': ('区', 'n'), 'subsector': ('亚区', 'n'),
'alba': ('白', 'mod'), 'cerebelli': ('小脑', 'n'), 'check': ('遏制', 'mod'),
'linea alba': ('白线', 'n'), 'tentorium cerebelli': ('小脑幕', 'n'),
'hyo-epiglottic': ('舌会厌', 'loc'), 'thyro-epiglottic': ('甲会厌', 'loc'),
'pre-hepatic': ('肝前', 'mod'), 'corpus cavernosum': ('海绵体', 'n'),
'corpus spongiosum': ('尿道海绵体', 'n'), 'diagonal': ('对角', 'mod'),
'autonomic': ('自主', 'mod'), 'flat': ('扁', 'mod'), 'pneumatized': ('含气', 'mod'),
'typical': ('典型', 'mod'), 'atypical': ('非典型', 'mod'), 'floating': ('浮', 'mod'),
'mucoid': ('黏液样', 'mod'), 'coli': ('结肠', 'n'), 'infrahyoid': ('舌骨下', 'loc'),
'suprahyoid': ('舌骨上', 'loc'), 'prevertebral': ('椎前', 'loc'), 'suboccipital': ('枕下', 'loc'),
'extra-ocular': ('眼外', 'loc'), 'extrahepatic': ('肝外', 'mod'), 'nonskeletal': ('非骨骼', 'mod'),
'loose': ('疏松', 'mod'), 'mesentery': ('肠系膜', 'n'),
'coeliac': ('腹腔', 'loc'), 'ii': ('Ⅱ', 'mod'), 'iii': ('Ⅲ', 'mod'), 'iv': ('Ⅳ', 'mod'),
'v': ('Ⅴ', 'mod'), 'vi': ('Ⅵ', 'mod'), 'vii': ('Ⅶ', 'mod'), 'viii': ('Ⅷ', 'mod'), 'ix': ('Ⅸ', 'mod'),
'biliary tree': ('胆管树', 'n'), 'hepatic biliary tree': ('肝胆管树', 'n'),
}

W2 = {k: v for k, v in W.items() if k not in DROP}
for k, v in EXTRA.items():
    if k not in DROP:
        W2[k] = v

def variants(w):
    out = [w]
    if w.endswith('ies'): out.append(w[:-3] + 'y')
    if w.endswith('ves'): out.append(w[:-3] + 'f')
    if w.endswith('ae'): out.append(w[:-2] + 'a')
    if w.endswith('es'): out.append(w[:-2])
    if w.endswith('s') and not w.endswith('ss'): out.append(w[:-1])
    return out

def lookup(token):
    for c in variants(token):
        if c in W2:
            return W2[c]
    return None

MISSING = []

# 自检：LOC 里声明为"部位词"的每个词都必须能查到译名，否则整条术语会因该词失败而放弃
UNRESOLVED_LOC = sorted(w for w in LOC if lookup(w) is None)
if UNRESOLVED_LOC:
    print('⚠ LOC 中缺少译名的词:', ' '.join(UNRESOLVED_LOC))


def tokenize(s):
    words = s.split()
    out, i = [], 0
    while i < len(words):
        found = None
        for L in (4, 3, 2, 1):
            if i + L <= len(words):
                raw = ' '.join(words[i:i + L])
                r = lookup(raw)
                if r:
                    t = r[1]
                    if L == 1 and raw in SIDE:
                        t = 'side'
                    elif L == 1 and raw in ORD:
                        t = 'ord'
                    elif any(v in LOC for v in variants(raw)):
                        t = 'loc'
                    found = ((r[0], t), L)
                    break
        if not found:
            MISSING.append(words[i])
            return None
        out.append(found[0])
        i += found[1]
    return out

DUP = re.compile(r'(.{1,2})\1')
def dedupe(s):
    prev = None
    while prev != s:
        prev = s
        s = DUP.sub(r'\1', s)
    return s

def simple(s):
    toks = tokenize(s)
    if not toks:
        return None
    g = lambda kinds: ''.join(x[0] for x in toks if x[1] in kinds)
    out = (g({'side'}) + g({'ord'}) + g({'loc'})
           + ''.join(x[0] for x in toks if x[1] not in ('side', 'ord', 'loc', 'm')) + g({'m'}))
    return dedupe(out)

def tr(s):
    # "A of B with C" -> B与C的A
    if ' with ' in s:
        left, c = s.split(' with ', 1)
        if ' of ' in left:
            head, b = left.split(' of ', 1)
            tb, tc, th = tr(b), tr(c), tr(head)
            if tb and tc and th:
                return dedupe(tb + '与' + tc + th)
        return None
    # "A of B to C" -> B至C的A
    if ' to ' in s:
        left, c = s.split(' to ', 1)
        if ' of ' in left:
            head, b = left.split(' of ', 1)
            tb, tc, th = tr(b), tr(c), tr(head)
            if tb and tc and th:
                return dedupe(tb + '至' + tc + th)
        return None
    if ' of ' in s:
        head, tail = s.split(' of ', 1)
        t, h = tr(tail), tr(head)
        return dedupe(t + h) if (t and h) else None
    return simple(s)

def translate(name):
    n = re.sub(r'\s+', ' ', name.lower().strip())
    n = re.sub(r'\s*\([^)]*\)', '', n)  # 去掉 "(in-vivo)" 一类限定语
    return tr(n)

if len(sys.argv) > 1:
    for t in sys.argv[1:]:
        print('%-42s toks=%s  => %s' % (t, tokenize(t.lower()), translate(t)))
    sys.exit()

atlas = json.load(open(os.path.join(ROOT, 'public/models/atlas.json')))
src = open(os.path.join(ROOT, 'app/i18n/anatomy-zh.ts')).read()
have = set(re.findall(r"(F[JM]A?\d+):", src.split('export const ANATOMY_ZH')[1]))
entries = [(p['id'], p['name']) for p in atlas['parts']] + [(c['id'], c['name']) for c in atlas['concepts']]
todo = [(i, n) for i, n in entries if i not in have]

ok, fail = [], []
for i, n in todo:
    zh = translate(n)
    (ok if zh else fail).append((i, n, zh) if zh else (i, n))

print('可翻译 %d / %d (%.0f%%)，放弃 %d' % (len(ok), len(todo), len(ok) / len(todo) * 100, len(fail)))
print('\n=== 随机样本 60 条 ===')
random.seed(11)
for i, n, zh in random.sample(ok, min(60, len(ok))):
    print('%-48s -> %s' % (n, zh))
import collections
print('\n=== 未识别词 top 90（按出现次数） ===')
for w, c in collections.Counter(MISSING).most_common(90):
    print('%s:%d' % (w, c), end='  ')
print()

ok.sort(key=lambda x: x[0])
lines = ["  %s: '%s'," % (i, zh) for i, n, zh in ok]
header = ("// 本文件由 scripts/translate-anatomy-zh.py 依据解剖学词表自动生成，请勿手工逐条修改。\n"
          "// 若某条术语译名不准：直接在 app/i18n/anatomy-zh.ts 里追加同 ID 条目覆盖（手写优先，见 index.ts）。\n"
          "// 若需批量改进：编辑 scripts/translate-anatomy-zh.py 词表后重新生成本文件。\n"
          "export const TERMS_ZH: Record<string, string> = {\n")
target = os.path.join(ROOT, 'app/i18n/terms-zh.ts')
open(target, 'w').write(header + "\n".join(lines) + "\n};\n")
print('\n已写入 app/i18n/terms-zh.ts：%d 条' % len(lines))
