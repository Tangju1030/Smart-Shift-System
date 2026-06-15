"""课表解析器 — 支持 docx Word课表和 xlsx Excel课表"""

import zipfile
import io
import re
from lxml import etree
import openpyxl


W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

# 课表节次关键词 → 值班节次
SLOT_KEYWORDS = {
    '1-2节': '第一节',
    '3-4节': '第二节',
    '5-6节': '第三节',
    '7-8节': '第四节',
}

WEEKDAY_MAP_CN = {
    '星期一': '周一', '星期二': '周二', '星期三': '周三',
    '星期四': '周四', '星期五': '周五', '星期六': '周六', '星期日': '周日',
}

DUTY_SLOTS = ['第一节', '第二节', '第三节', '第四节']
WEEKDAYS = ['周一', '周二', '周三', '周四', '周五']


def parse_docx_schedule(file_bytes: bytes, filename: str, week_no: int | None = None) -> dict:
    """
    解析 Word 课表文件

    返回: {name: str, availability: {weekday: {slot: True=空闲}}}
    """
    name = _extract_name_from_filename(filename)

    with zipfile.ZipFile(io.BytesIO(file_bytes), 'r') as z:
        xml = z.read('word/document.xml')

    tree = etree.fromstring(xml)

    # 尝试从文档内容提取姓名
    if not name:
        all_texts = []
        for elem in tree.iter():
            if elem.tag == f'{{{W}}}t' and elem.text:
                all_texts.append(elem.text)
        full = ''.join(all_texts)
        name_m = re.search(r'姓名：(.+?)[\s　]', full)
        name = name_m.group(1).strip() if name_m else None

    if not name:
        return {"name": None, "error": "无法识别姓名", "availability": {}}

    # 找课表表格
    tables = tree.findall(f'.//{{{W}}}tbl')
    availability = {wd: {s: True for s in DUTY_SLOTS} for wd in WEEKDAYS}
    # True = 空闲可排班

    for tbl in tables:
        rows = tbl.findall(f'.//{{{W}}}tr')
        if not rows:
            continue

        # 尝试识别表头中的星期列
        header_cells = _extract_row_text(rows[0])
        col_to_wd = {}
        for ci, text in enumerate(header_cells[:7]):
            for cn, abbr in WEEKDAY_MAP_CN.items():
                if cn in text:
                    col_to_wd[ci] = abbr
                    break

        if not col_to_wd:
            continue  # 不是课表表格

        for row in rows[1:]:
            cells = _extract_row_text(row)
            # 确定此行是哪个时段
            slot = None
            for ci, text in enumerate(cells):
                for kw, s in SLOT_KEYWORDS.items():
                    if kw in text:
                        slot = s
                        break
                if slot:
                    break
            if not slot:
                continue

            # 标记有课的星期
            for ci, text in enumerate(cells[:7]):
                if ci in col_to_wd:
                    wd = col_to_wd[ci]
                    if wd in availability and text.strip() and len(text.strip()) >= 2:
                        # 检查是否在当前周有课
                        if _is_in_week(text, week_no):
                            availability[wd][slot] = False

    return {"name": name, "error": None, "availability": availability}


def parse_xlsx_schedule(file_bytes: bytes) -> list[dict]:
    """
    解析 Excel 课表（格式：姓名 | 周一1-2节 | 周一3-4节 | ...）

    返回: [{name: str, availability: {weekday: {slot: bool}}}]
    """
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        return []

    header = [str(c).strip() if c else "" for c in rows[0]]
    # 建立列映射：列名 → (weekday, slot)
    col_map = {}
    for ci, h in enumerate(header):
        for wd in WEEKDAYS:
            for slot in DUTY_SLOTS:
                if wd in h and _slot_label(slot) in h:
                    col_map[ci] = (wd, slot)
                    break

    results = []
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        name = str(row[0]).strip()
        availability = {wd: {s: True for s in DUTY_SLOTS} for wd in WEEKDAYS}
        for ci, (wd, slot) in col_map.items():
            if ci < len(row) and row[ci]:
                val = str(row[ci]).strip()
                if val and val not in ('无', '-', '×', '✗', 'x', '空'):
                    availability[wd][slot] = False
        results.append({"name": name, "availability": availability})

    return results


def _extract_row_text(row) -> list[str]:
    """提取Word表格行的单元格文本"""
    cells = row.findall(f'.//{{{W}}}tc')
    result = []
    for cell in cells[:7]:
        texts = [t.text for t in cell.findall(f'.//{{{W}}}t') if t.text]
        result.append(''.join(texts).replace('\xa0', ' ').strip())
    return result


def _extract_name_from_filename(filename: str) -> str | None:
    """从文件名提取姓名"""
    fn = filename.replace('.docx', '').replace('.doc', '').strip()
    # 纯中文名
    if re.match(r'^[一-龥]{2,4}$', fn):
        return fn
    # 去掉课表等前缀
    cleaned = re.sub(r'^课表[-_\s]*', '', fn)
    cleaned = re.sub(r'[-_\s]*课表$', '', cleaned)
    if re.match(r'^[一-龥]{2,4}$', cleaned.strip()):
        return cleaned.strip()
    # 提取连续汉字
    matches = re.findall(r'[一-龥]{2,4}', fn)
    non_names = {'课表', '我的', '个人', '同学', '班级'}
    for m in matches:
        if m not in non_names:
            return m
    return None


def _is_in_week(cell_text: str, week_no: int | None) -> bool:
    """判断课程是否在指定周有课"""
    if week_no is None:
        return True  # 未指定周次，视为全周有课
    # 匹配 (X周) 或 (X~Y周) 等格式
    week_ranges = re.findall(r'\(([\d,~]+)周\)', cell_text)
    if not week_ranges:
        return True  # 无周次标注，视为全周有课
    for range_str in week_ranges:
        parts = range_str.split(',')
        for part in parts:
            if '~' in part:
                a, b = part.split('~')
                if week_no >= int(a) and week_no <= int(b):
                    return True
            else:
                if int(part) == week_no:
                    return True
    return False


def _slot_label(slot: str) -> str:
    """时段名 → 课表标签"""
    mapping = {'第一节': '1-2节', '第二节': '3-4节', '第三节': '5-6节', '第四节': '7-8节'}
    return mapping.get(slot, slot)
