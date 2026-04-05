import cv2
import re
from Tool.WindowsAPI import grab_screen
from Tool.GameProfile import get_active_profile

try:
    import pytesseract
except Exception:
    pytesseract = None


def _to_bgr(frame):
    if frame is None or frame.size == 0:
        return None
    if len(frame.shape) == 3 and frame.shape[2] == 4:
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    return frame


def _extract_text(frame_bgr):
    if pytesseract is None:
        return ""
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    txt_cn = pytesseract.image_to_string(binary, lang="chi_sim+eng", config="--psm 6")
    txt_en = pytesseract.image_to_string(binary, lang="eng", config="--psm 6")
    return (txt_cn or "") + "\n" + (txt_en or "")


def detect_keywords_from_frame(frame, keywords):
    frame_bgr = _to_bgr(frame)
    if frame_bgr is None:
        return set(), ""
    text = _extract_text(frame_bgr)
    if not text:
        return set(), ""
    normalized = re.sub(r"\s+", "", text)
    found = set()
    for kw in keywords:
        if kw == "L":
            if re.search(r"(^|[^A-Za-z])L([^A-Za-z]|$)", text):
                found.add(kw)
        elif kw in text or kw in normalized:
            found.add(kw)
    return found, text


def capture_and_detect_keywords(keywords):
    profile = get_active_profile()
    frame = grab_screen(profile.station_size)
    return detect_keywords_from_frame(frame, keywords)
