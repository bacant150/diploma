from __future__ import annotations

import re
from typing import Dict, List, Tuple

PURPOSES = ["gaming", "office", "study", "creator"]

_NORMALIZATION_RULES: list[tuple[str, str]] = [
    (r"[`’ʼ']", "'"),
    (r"\bm\.?e\.?\s*doc\b", " medoc "),
    (r"\bмедок\b|\bmedoc\b", " medoc "),
    (r"\b1\s*[сc]\b|\b1c\b|\b1с\b|\bbas\b|\bбас\b", " bas "),
    (r"\bклієнт[- ]?банк\b|\bclient[- ]?bank\b", " clientbank "),
    (r"\bword\b|\bворд\b", " word "),
    (r"\bexcel\b|\bексел\w*\b", " excel "),
    (r"\bpower\s*point\b|\bpowerpoint\b", " powerpoint "),
    (r"\bpdf\b", " pdf "),
    (r"\bcrm\b", " crm "),
    (r"\bemail\b|\be-mail\b|\bпошт\w*\b", " email "),
    (r"\bzoom\b", " zoom "),
    (r"\bgoogle\s*meet\b|\bmeet\b", " meet "),
    (r"\bclassroom\b", " classroom "),
    (r"\bmoodle\b", " moodle "),
    (r"\bvscode\b|\bvs\s*code\b|\bvisual\s*studio\s*code\b", " vscode "),
    (r"\bpython\b|\bпайтон\b", " python "),
    (r"\bc\+\+\b", " cpp "),
    (r"\bjava\b", " java "),
    (r"\bprogramming\b|\bпрограмуван\w*\b|\bкодинг\b|\bкодуван\w*\b|\bкодити\b", " programming "),
    (r"\bстудент\w*\b|\bшколяр\w*\b|\bнавчан\w*\b|\bурок\w*\b|\bлекці\w*\b|\bдомашн\w*\b|\bуніверситет\w*\b|\bунівер\b", " study "),
    (r"\bblender\b|\bблендер\b", " blender "),
    (r"\bautocad\b", " autocad "),
    (r"\bsolidworks\b", " solidworks "),
    (r"\b3\s*d\b|\b3д\b|\b3-d\b", " 3d "),
    (r"\bafter\s*effects\b", " aftereffects "),
    (r"\bpremiere\s*pro\b|\bpremiere\b", " premierepro "),
    (r"\bdavinci\s*resolve\b|\bdavinci\b", " davinciresolve "),
    (r"\bphotoshop\b", " photoshop "),
    (r"\blightroom\b", " lightroom "),
    (r"\billustrator\b", " illustrator "),
    (r"\bfigma\b", " figma "),
    (r"\bmaya\b", " maya "),
    (r"\b3ds\s*max\b", " max3d "),
    (r"\bunreal\s*engine\b", " unrealengine "),
    (r"\bvideo\s*editing\b|\bвідеомонтаж\b|\bмонтаж\w*\b", " videoedit "),
    (r"\bдизайн\w*\b|\bграфік\w*\b|\bрендер\w*\b|\банімац\w*\b|\bконтент\w*\b", " creator "),
    (r"\bdota\s*2\b|\bdota2\b|\bдота\s*2\b|\bдоту\s*2\b|\bдота\b|\bдоту\b", " dota2 "),
    (r"\bcs\s*2\b|\bcs2\b|\bcounter\s*strike\s*2\b|\bcounter\s*strike\b|\bконтра\b|\bкс\s*2\b|\bкс2\b|\bкс\b", " cs2 "),
    (r"\bvalorant\b", " valorant "),
    (r"\bleague\s*of\s*legends\b|\blol\b", " lol "),
    (r"\bfortnite\b", " fortnite "),
    (r"\bpubg\b", " pubg "),
    (r"\bwarzone\b|\bcall\s*of\s*duty\b", " warzone "),
    (r"\bapex\s*legends\b|\bapex\b", " apex "),
    (r"\bcyberpunk\s*2077\b|\bcyberpunk\b", " cyberpunk "),
    (r"\bgta\s*5\b|\bgta\s*v\b|\bgta\b", " gta5 "),
    (r"\bforza\s*horizon\b|\bforza\b", " forza "),
    (r"\bminecraft\b", " minecraft "),
    (r"\broblox\b", " roblox "),
    (r"\besports\b|\bкіберспорт\w*\b", " esports "),
    (r"\bfps\b|\b144\s*fps\b|\b240\s*fps\b|\b60\s*fps\b", " fps "),
    (r"\bстрим\w*\b|\bstream\w*\b", " stream "),
    (r"\bігров\w*\b|\bігр\w*\b|\bгра\w*\b|\bгри\b|\bгру\b|\bграти\b|\bпограти\b", " gaming "),
    (r"\bофіс\w*\b|\bдокумент\w*\b|\bтаблиц\w*\b|\bзвіт\w*\b|\bбухгалтер\w*\b|\bрахунк\w*\b|\bнакладн\w*\b|\bакт\w*\b|\bдоговор\w*\b", " office "),
]

KEYWORD_HINTS: Dict[str, List[Tuple[str, str, float]]] = {
    "gaming": [
        ("dota2", r"\bdota2\b", 4.5), ("cs2", r"\bcs2\b", 4.5), ("valorant", r"\bvalorant\b", 4.0),
        ("fortnite", r"\bfortnite\b", 3.8), ("warzone", r"\bwarzone\b", 3.8), ("pubg", r"\bpubg\b", 3.5),
        ("apex", r"\bapex\b", 3.5), ("cyberpunk", r"\bcyberpunk\b", 3.8), ("gta5", r"\bgta5\b", 3.5),
        ("esports", r"\besports\b", 2.8), ("fps", r"\bfps\b", 2.2), ("stream", r"\bstream\b", 1.6),
        ("gaming", r"\bgaming\b", 2.4),
    ],
    "office": [
        ("medoc", r"\bmedoc\b", 4.8), ("bas", r"\bbas\b", 4.5), ("clientbank", r"\bclientbank\b", 4.2),
        ("excel", r"\bexcel\b", 2.8), ("word", r"\bword\b", 2.0), ("powerpoint", r"\bpowerpoint\b", 1.8),
        ("crm", r"\bcrm\b", 2.4), ("email", r"\bemail\b", 1.8), ("office", r"\boffice\b", 2.3), ("pdf", r"\bpdf\b", 1.0),
    ],
    "study": [
        ("study", r"\bstudy\b", 3.0), ("zoom", r"\bzoom\b", 2.7), ("meet", r"\bmeet\b", 2.6),
        ("classroom", r"\bclassroom\b", 2.8), ("moodle", r"\bmoodle\b", 2.8), ("vscode", r"\bvscode\b", 2.3),
        ("python", r"\bpython\b", 2.2), ("cpp", r"\bcpp\b", 2.0), ("java", r"\bjava\b", 2.0), ("programming", r"\bprogramming\b", 2.2),
    ],
    "creator": [
        ("blender", r"\bblender\b", 4.8), ("premierepro", r"\bpremierepro\b", 4.5), ("aftereffects", r"\baftereffects\b", 4.5),
        ("davinciresolve", r"\bdavinciresolve\b", 4.2), ("photoshop", r"\bphotoshop\b", 3.0), ("lightroom", r"\blightroom\b", 2.8),
        ("illustrator", r"\billustrator\b", 2.8), ("autocad", r"\bautocad\b", 3.2), ("solidworks", r"\bsolidworks\b", 3.5),
        ("maya", r"\bmaya\b", 3.3), ("max3d", r"\bmax3d\b", 3.3), ("unrealengine", r"\bunrealengine\b", 3.0),
        ("videoedit", r"\bvideoedit\b", 3.6), ("creator", r"\bcreator\b", 2.6), ("3d", r"\b3d\b", 2.8),
        ("figma", r"\bfigma\b", 2.3),
    ],
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("ё", "е")
    text = re.sub(r"[^\w\s\+\-\.'’ʼ`]", " ", text, flags=re.UNICODE)
    for pattern, replacement in _NORMALIZATION_RULES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text, flags=re.UNICODE).strip()
    return text


def keyword_scores(text: str) -> tuple[Dict[str, float], Dict[str, List[str]]]:
    scores: Dict[str, float] = {label: 0.0 for label in PURPOSES}
    matched: Dict[str, List[str]] = {label: [] for label in PURPOSES}

    for label, rules in KEYWORD_HINTS.items():
        for name, pattern, weight in rules:
            if re.search(pattern, text, flags=re.IGNORECASE):
                scores[label] += weight
                matched[label].append(name)
    return scores, matched


def to_probabilities(raw_scores: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(value, 0.0) for value in raw_scores.values())
    if total <= 0:
        return {label: 0.0 for label in PURPOSES}
    return {label: max(raw_scores[label], 0.0) / total for label in PURPOSES}


def blend_probabilities(model_probs: Dict[str, float], keyword_probs: Dict[str, float], *, model_weight: float = 0.78, keyword_weight: float = 0.22) -> Dict[str, float]:
    has_keywords = sum(keyword_probs.values()) > 0
    kw_w = keyword_weight if has_keywords else 0.0
    mdl_w = 1.0 - kw_w
    return {label: mdl_w * model_probs.get(label, 0.0) + kw_w * keyword_probs.get(label, 0.0) for label in PURPOSES}


def sorted_candidates(probabilities: Dict[str, float]) -> List[Tuple[str, float]]:
    return sorted(probabilities.items(), key=lambda item: item[1], reverse=True)


def strong_keyword_override(raw_keyword_scores: Dict[str, float]) -> tuple[str | None, float | None]:
    ranked = sorted(raw_keyword_scores.items(), key=lambda item: item[1], reverse=True)
    if not ranked or ranked[0][1] <= 0:
        return None, None
    top_label, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    if top_score >= 4.2 and (top_score - second_score) >= 2.0:
        confidence = min(0.97, 0.72 + top_score / 12.0)
        return top_label, confidence
    return None, None
