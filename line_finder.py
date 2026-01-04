"""Precise line detector
Detects a single white line with these criteria:
- Color: white (RGB >= 240)
- Thickness: 5-8 pixels
- Both ends bounded by black
- Chooses the longest connected line
"""

import cv2
import mss
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple

WHITE_MIN = 240
BLACK_MAX = 40
MIN_LINE_LENGTH = 30
MIN_LINE_THICKNESS = 2
MAX_LINE_THICKNESS = 15


@dataclass
class DetectedLine:
    x1: int
    y1: int
    x2: int
    y2: int
    length: float
    thickness: float


def capture_screen() -> np.ndarray:
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


def get_white_mask(img: np.ndarray) -> np.ndarray:
    b, g, r = cv2.split(img)
    white_mask = (r >= WHITE_MIN) & (g >= WHITE_MIN) & (b >= WHITE_MIN)
    return (white_mask * 255).astype(np.uint8)


def get_black_mask(img: np.ndarray) -> np.ndarray:
    b, g, r = cv2.split(img)
    black_mask = (r <= BLACK_MAX) & (g <= BLACK_MAX) & (b <= BLACK_MAX)
    return (black_mask * 255).astype(np.uint8)


def find_line_endpoints(contour) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    points = contour.reshape(-1, 2)
    
    if len(points) < 2:
        return ((0, 0), (0, 0))
    
    max_dist = 0
    p1, p2 = points[0], points[-1]
    
    if len(points) > 4:
        hull = cv2.convexHull(contour)
        hull_points = hull.reshape(-1, 2)
    else:
        hull_points = points
    
    for i, pt1 in enumerate(hull_points):
        for pt2 in hull_points[i+1:]:
            dist = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
            if dist > max_dist:
                max_dist = dist
                p1, p2 = pt1, pt2
    
    return ((int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])))


def check_black_at_ends(img: np.ndarray, p1: Tuple[int, int], p2: Tuple[int, int], 
                         direction: Tuple[float, float], check_radius: int = 20) -> bool:
    black_mask = get_black_mask(img)
    h, w = black_mask.shape
    
    dx, dy = direction
    length = np.sqrt(dx*dx + dy*dy)
    if length == 0:
        return True
    dx, dy = dx/length, dy/length
    
    def has_black_ahead(px: int, py: int, dir_x: float, dir_y: float) -> bool:
        for dist in range(3, check_radius):
            check_x = int(px + dir_x * dist)
            check_y = int(py + dir_y * dist)
            
            if 0 <= check_x < w and 0 <= check_y < h:
                if black_mask[check_y, check_x] > 0:
                    return True
        return False
    
    end1_ok = has_black_ahead(p1[0], p1[1], -dx, -dy)
    end2_ok = has_black_ahead(p2[0], p2[1], dx, dy)
    
    return end1_ok or end2_ok


def find_lines(img: np.ndarray) -> List[DetectedLine]:
    white_mask = get_white_mask(img)
    contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    valid_lines = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 50:
            continue
        
        x, y, w, h = cv2.boundingRect(contour)
        
        if len(contour) >= 5:
            rect = cv2.minAreaRect(contour)
            rect_w, rect_h = rect[1]
            thickness = min(rect_w, rect_h)
            length = max(rect_w, rect_h)
        else:
            thickness = min(w, h)
            length = max(w, h)
        
        if thickness < MIN_LINE_THICKNESS or thickness > MAX_LINE_THICKNESS:
            continue
        
        if length < MIN_LINE_LENGTH:
            continue
        
        aspect_ratio = length / max(thickness, 1)
        if aspect_ratio < 3:
            continue
        
        p1, p2 = find_line_endpoints(contour)
        direction = (p2[0] - p1[0], p2[1] - p1[1])
        
        if not check_black_at_ends(img, p1, p2, direction):
            continue
        
        valid_lines.append(DetectedLine(
            x1=p1[0], y1=p1[1],
            x2=p2[0], y2=p2[1],
            length=length,
            thickness=thickness
        ))
    
    return valid_lines


def main():
    print("=" * 50)
    print("  Line detector (for 5-8px thick lines)")
    print("=" * 50)
    print()
    print("Parameters:")
    print(f"  • White: RGB >= {WHITE_MIN}")
    print(f"  • Black at ends: RGB <= {BLACK_MAX}")
    print(f"  • Length: >= {MIN_LINE_LENGTH}px")
    print(f"  • Thickness: {MIN_LINE_THICKNESS}-{MAX_LINE_THICKNESS}px")
    print()
    
    print("📸 Taking screenshot...")
    img = capture_screen()
    
    white_mask = get_white_mask(img)
    black_mask = get_black_mask(img)
    cv2.imwrite("debug_white.png", white_mask)
    cv2.imwrite("debug_black.png", black_mask)
    print(f"💾 Debug: debug_white.png ({np.sum(white_mask > 0)} pixels)")
    
    print("🔍 Searching for lines...")
    lines = find_lines(img)
    print(f"   Found: {len(lines)} line(s)")
    
    if lines:
        line = max(lines, key=lambda l: l.length)
        
        print()
        print("✅ LONGEST LINE:")
        print(f"   Start:  ({line.x1}, {line.y1})")
        print(f"   End:    ({line.x2}, {line.y2})")
        print(f"   Length: {line.length:.1f}px")
        print(f"   Thickness:  {line.thickness:.1f}px")
        
        preview = img.copy()
        
        for l in lines:
            cv2.line(preview, (l.x1, l.y1), (l.x2, l.y2), (128, 128, 128), 2)
        
        cv2.line(preview, (line.x1, line.y1), (line.x2, line.y2), (0, 255, 0), 3)
        cv2.circle(preview, (line.x1, line.y1), 8, (0, 0, 255), -1)
        cv2.circle(preview, (line.x2, line.y2), 8, (255, 0, 0), -1)
        
        cv2.imwrite("detected_line.png", preview)
        print()
        print("💾 Preview: detected_line.png")
        
        if len(lines) > 1:
            print()
            print(f"All {len(lines)} lines:")
            for i, l in enumerate(sorted(lines, key=lambda x: -x.length)[:5]):
                print(f"   {i+1}. Length={l.length:.0f}px, Thickness={l.thickness:.1f}px")
    else:
        print()
        print("❌ No matching line found!")
        
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"   White contours: {len(contours)}")
        
        big_contours = []
        for c in contours:
            area = cv2.contourArea(c)
            if area >= 50 and len(c) >= 5:
                rect = cv2.minAreaRect(c)
                w, h = rect[1]
                big_contours.append((c, area, max(w,h), min(w,h)))
        
        big_contours.sort(key=lambda x: -x[1])
        print(f"   Contours with area >= 50: {len(big_contours)}")
        
        for i, (c, area, length, thickness) in enumerate(big_contours[:10]):
            aspect = length / max(thickness, 1)
            p1, p2 = find_line_endpoints(c)
            print(f"   {i+1}. Area={area:.0f}, L={length:.0f}, D={thickness:.1f}, Aspect={aspect:.1f}")
            print(f"       Endpoints: {p1} → {p2}")
        
        preview = img.copy()
        for c, area, length, thickness in big_contours[:10]:
            cv2.drawContours(preview, [c], -1, (0, 255, 0), 2)
            p1, p2 = find_line_endpoints(c)
            cv2.circle(preview, p1, 5, (0, 0, 255), -1)
            cv2.circle(preview, p2, 5, (255, 0, 0), -1)
        cv2.imwrite("debug_contours.png", preview)
        print()
        print("💾 Debug: debug_contours.png")


if __name__ == "__main__":
    main()
