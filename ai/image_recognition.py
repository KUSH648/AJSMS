import os
import base64
import io
import numpy as np
from PIL import Image

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

CATEGORIES = ['Ring', 'Necklace', 'Bracelet', 'Earrings', 'Other']


def segment_object(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        mask = np.zeros_like(gray)
        cv2.drawContours(mask, [largest], -1, 255, -1)
        return mask, largest
    return thresh, None


def extract_features(img_bgr):
    features = {}
    h, w = img_bgr.shape[:2]
    features['aspect_ratio'] = w / (h + 1e-5)

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    features['brightness'] = float(gray.mean() / 255.0)
    features['contrast'] = float(gray.std() / 255.0)

    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    avg_hue = hsv[:, :, 0].mean()
    avg_sat = hsv[:, :, 1].mean() / 255.0
    avg_val = hsv[:, :, 2].mean() / 255.0
    features['avg_hue'] = float(avg_hue)
    features['avg_saturation'] = float(avg_sat)
    features['avg_value'] = float(avg_val)
    gold_mask = cv2.inRange(hsv, np.array([15, 30, 100]), np.array([35, 255, 255]))
    features['gold_ratio'] = float(gold_mask.sum() / (h * w * 255 + 1e-5))
    white_mask = cv2.inRange(hsv, np.array([0, 0, 180]), np.array([180, 30, 255]))
    features['white_ratio'] = float(white_mask.sum() / (h * w * 255 + 1e-5))
    silver_mask = cv2.inRange(hsv, np.array([0, 0, 80]), np.array([180, 30, 180]))
    features['silver_ratio'] = float(silver_mask.sum() / (h * w * 255 + 1e-5))

    edges = cv2.Canny(gray, 30, 100)
    features['edge_density'] = float(edges.sum() / (edges.size + 1e-5))

    mask, largest_contour = segment_object(img_bgr)
    if largest_contour is not None:
        obj_area = cv2.contourArea(largest_contour)
        features['obj_fill'] = float(obj_area / (h * w + 1e-5))
        perim = cv2.arcLength(largest_contour, True)
        features['circularity'] = float((4 * np.pi * obj_area) / (perim * perim + 1e-5))
        x, y, cw, ch = cv2.boundingRect(largest_contour)
        features['bbox_aspect'] = cw / (ch + 1e-5)
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)
        features['solidity'] = float(obj_area / (hull_area + 1e-5))
        moments = cv2.moments(largest_contour)
        if moments['m20'] != 0 and moments['m02'] != 0:
            features['elongation'] = float(min(moments['m20'], moments['m02']) / (max(moments['m20'], moments['m02']) + 1e-5))
        else:
            features['elongation'] = 0.5
    else:
        features['obj_fill'] = 0.1
        features['circularity'] = 0.0
        features['bbox_aspect'] = features['aspect_ratio']
        features['solidity'] = 0.5
        features['elongation'] = 0.5

    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    vertical_edges = cv2.Sobel(bw, cv2.CV_64F, 1, 0, ksize=3)
    horizontal_edges = cv2.Sobel(bw, cv2.CV_64F, 0, 1, ksize=3)
    vert_strength = np.abs(vertical_edges).mean()
    horz_strength = np.abs(horizontal_edges).mean()
    features['vert_horz_ratio'] = float((vert_strength + 1e-5) / (horz_strength + 1e-5))

    return features


def compute_scores(features):
    scores = {c: 0.0 for c in CATEGORIES}
    ar = features['aspect_ratio']
    circ = features['circularity']
    bright = features['brightness']
    sat = features['avg_saturation']
    gold_r = features['gold_ratio']
    white_r = features['white_ratio']
    silver_r = features['silver_ratio']
    fill = features['obj_fill']
    solidity = features['solidity']
    edge = features['edge_density']
    vert_horz = features['vert_horz_ratio']
    elon = features['elongation']
    contrast = features['contrast']

    ar_score = 1.0 - abs(ar - 1.0) / 2.0
    ar_score = max(0.0, min(1.0, ar_score))

    if gold_r > 0.05:
        scores['Ring'] += 0.15 * min(gold_r * 3, 1.0)
        scores['Bracelet'] += 0.10 * min(gold_r * 2, 1.0)
        scores['Earrings'] += 0.05 * min(gold_r * 2, 1.0)
    if white_r > 0.05:
        scores['Ring'] += 0.10 * min(white_r * 3, 1.0)
        scores['Necklace'] += 0.05 * min(white_r * 2, 1.0)
    if silver_r > 0.1:
        scores['Bracelet'] += 0.10 * min(silver_r * 2, 1.0)

    if circ > 0.3 and ar_score > 0.6:
        ring_score = circ * 0.4 + ar_score * 0.3 + solidity * 0.3
        scores['Ring'] += ring_score

    if ar > 1.3:
        necklace_score = min((ar - 1.3) / 1.5, 1.0) * 0.5
        if bright < 0.7:
            necklace_score += 0.3
        scores['Necklace'] += necklace_score

    if 1.0 < ar < 1.8 and circ < 0.5:
        bangle_score = 0.4 * (1.0 - abs(circ - 0.25) / 0.5) + 0.3 * min(ar / 2.0, 1.0)
        scores['Bracelet'] += max(0, bangle_score)

    if ar < 0.9:
        earring_score = (1.0 - ar) * 0.6 + min(edge, 0.3)
        if vert_horz > 1.5:
            earring_score += 0.2
        scores['Earrings'] += earring_score

    if fill < 0.15 or (edge > 0.25 and bright < 0.4):
        scores['Other'] += 0.6

    min_val = min(scores.values())
    if min_val < 0:
        for c in scores:
            scores[c] -= min_val
    max_val = max(scores.values())
    if max_val > 0:
        for c in scores:
            scores[c] = round(scores[c] / max_val, 2)
    else:
        for c in scores:
            scores[c] = 0.2

    return scores


def heuristic_classify(features):
    scores = compute_scores(features)
    sorted_cats = sorted(scores.items(), key=lambda x: -x[1])
    return sorted_cats[0][0], sorted_cats[0][1], scores


def classify_from_array(img_bgr):
    img_bgr = cv2.resize(img_bgr, (224, 224))
    features = extract_features(img_bgr)
    category, conf, scores = heuristic_classify(features)
    conf = round(conf * 100, 1)
    scores = {c: round(v * 100, 1) for c, v in scores.items()}
    return category, conf, scores


def classify_image_file(filepath):
    if not CV2_AVAILABLE:
        return _fallback_classify(filepath)
    try:
        img = cv2.imread(filepath)
        if img is None:
            return {'error': 'Could not read image file.', 'category': 'Unknown'}
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        category, conf, scores = classify_from_array(img)
        return {'category': category, 'confidence': conf, 'scores': scores, 'error': None}
    except Exception as e:
        return {'error': str(e), 'category': 'Unknown'}


def classify_image_bytes(image_bytes):
    if not CV2_AVAILABLE:
        return _fallback_classify_bytes(image_bytes)
    try:
        np_arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            return {'error': 'Could not decode image.', 'category': 'Unknown'}
        category, conf, scores = classify_from_array(img)
        return {'category': category, 'confidence': conf, 'scores': scores, 'error': None}
    except Exception as e:
        return {'error': str(e), 'category': 'Unknown'}


def _fallback_classify(filepath):
    try:
        img = Image.open(filepath).convert('RGB').resize((100, 100))
        return _pil_classify(img)
    except Exception as e:
        return {'error': str(e), 'category': 'Unknown'}


def _fallback_classify_bytes(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB').resize((100, 100))
        return _pil_classify(img)
    except Exception as e:
        return {'error': str(e), 'category': 'Unknown'}


def _pil_classify(pil_img):
    arr = np.array(pil_img)
    h, w, _ = arr.shape
    ar = w / (h + 1e-5)
    gray = np.mean(arr, axis=2)
    bright = gray.mean() / 255.0
    r, g, b = arr[:, :, 0].mean(), arr[:, :, 1].mean(), arr[:, :, 2].mean()
    warmth = (r - b) / 255.0
    if bright > 0.55 and 0.7 < ar < 1.4:
        cat, conf = 'Ring', 0.65
    elif ar < 0.8:
        cat, conf = 'Earrings', 0.58
    elif ar > 1.5:
        cat, conf = 'Necklace', 0.60
    elif 0.85 < ar < 1.15:
        cat, conf = 'Ring', 0.62
    elif warmth > 0.1:
        cat, conf = 'Ring', 0.55
    elif bright > 0.6:
        cat, conf = 'Ring', 0.50
    else:
        cat, conf = 'Bracelet', 0.55
    conf = round(conf * 100, 1)
    scores = {c: round(0.10 * 100, 1) for c in CATEGORIES}
    scores[cat] = conf
    return {'category': cat, 'confidence': conf, 'scores': scores, 'error': None}
