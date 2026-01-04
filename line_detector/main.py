"""8 Ball Pool trajectory overlay
Detects the target line and draws its extended trajectory on screen.
Transparent click-through overlay.
"""

import ctypes
import sys
import tkinter as tk

import cv2
import mss
import numpy as np

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020

SCAN_INTERVAL_MS = 1
WHITE_MIN = 240
BLACK_MAX = 40
MIN_LINE_LENGTH = 30
MIN_LINE_THICKNESS = 2
MAX_LINE_THICKNESS = 15
EXTEND_LENGTH = 2000
LINE_COLOR = "#00FF00"
LINE_WIDTH = 3


class LineDetector:
    """Erkennt weiße Linien im Bild"""
    
    @staticmethod
    def get_white_mask(img: np.ndarray) -> np.ndarray:
        b, g, r = cv2.split(img)
        white_mask = (r >= WHITE_MIN) & (g >= WHITE_MIN) & (b >= WHITE_MIN)
        return (white_mask * 255).astype(np.uint8)
    
    @staticmethod
    def get_black_mask(img: np.ndarray) -> np.ndarray:
        b, g, r = cv2.split(img)
        black_mask = (r <= BLACK_MAX) & (g <= BLACK_MAX) & (b <= BLACK_MAX)
        return (black_mask * 255).astype(np.uint8)
    
    @staticmethod
    def find_line_endpoints(contour):
        points = contour.reshape(-1, 2)
        if len(points) < 2:
            return ((0, 0), (0, 0))
        
        if len(points) > 4:
            hull = cv2.convexHull(contour)
            hull_points = hull.reshape(-1, 2)
        else:
            hull_points = points
        
        max_dist = 0
        p1, p2 = points[0], points[-1]
        
        for i, pt1 in enumerate(hull_points):
            for pt2 in hull_points[i+1:]:
                dist = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                if dist > max_dist:
                    max_dist = dist
                    p1, p2 = pt1, pt2
        
        return ((int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])))
    
    @staticmethod
    def check_black_at_ends(img: np.ndarray, p1, p2, direction, check_radius=20):
        black_mask = LineDetector.get_black_mask(img)
        h, w = black_mask.shape
        
        dx, dy = direction
        length = np.sqrt(dx*dx + dy*dy)
        if length == 0:
            return True
        dx, dy = dx/length, dy/length
        
        def has_black_ahead(px, py, dir_x, dir_y):
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
    
    @staticmethod
    def detect(img: np.ndarray):
        white_mask = LineDetector.get_white_mask(img)
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        valid_lines = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 50:
                continue
            
            if len(contour) >= 5:
                rect = cv2.minAreaRect(contour)
                rect_w, rect_h = rect[1]
                thickness = min(rect_w, rect_h)
                length = max(rect_w, rect_h)
            else:
                x, y, w, h = cv2.boundingRect(contour)
                thickness = min(w, h)
                length = max(w, h)
            
            if thickness < MIN_LINE_THICKNESS or thickness > MAX_LINE_THICKNESS:
                continue
            
            if length < MIN_LINE_LENGTH:
                continue
            
            aspect_ratio = length / max(thickness, 1)
            if aspect_ratio < 3:
                continue
            
            p1, p2 = LineDetector.find_line_endpoints(contour)
            direction = (p2[0] - p1[0], p2[1] - p1[1])
            
            if not LineDetector.check_black_at_ends(img, p1, p2, direction):
                continue
            
            valid_lines.append((p1[0], p1[1], p2[0], p2[1], length))
        
        if not valid_lines:
            return None
        
        # Längste Linie zurückgeben
        best = max(valid_lines, key=lambda l: l[4])
        return (best[0], best[1], best[2], best[3])


class TrajectoryOverlay:
    """Transparentes Overlay das die verlängerte Linie anzeigt"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Trajectory Overlay")
        
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "black")
        self.root.config(bg="black")
        
        self.canvas = tk.Canvas(
            self.root,
            width=self.screen_width,
            height=self.screen_height,
            bg="black",
            highlightthickness=0
        )
        self.canvas.pack()
        
        self.sct = mss.mss()
        
        self.root.after(100, self.make_click_through)
        self.root.after(500, self.update)
        self.root.bind("<Escape>", lambda e: self.quit())
        
        print("🎱 Trajectory Overlay started!")
        print("   ESC = Exit")
    
    def make_click_through(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            new_style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            print("✅ Click-through aktiviert")
        except Exception as e:
            print(f"⚠️ Click-through error: {e}")
    
    def capture_screen(self):
        monitor = self.sct.monitors[1]
        screenshot = self.sct.grab(monitor)
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    def extend_line_full(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        length = np.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return (x1, y1, x2, y2)
        
        # Normalisieren
        dx /= length
        dy /= length
        
        # 2000 Pixel in BEIDE Richtungen verlängern
        new_x1 = int(x1 - dx * EXTEND_LENGTH)
        new_y1 = int(y1 - dy * EXTEND_LENGTH)
        new_x2 = int(x2 + dx * EXTEND_LENGTH)
        new_y2 = int(y2 + dy * EXTEND_LENGTH)
        
        return (new_x1, new_y1, new_x2, new_y2)
    
    def draw_line(self, x1, y1, x2, y2):
        self.canvas.delete("all")
        self.canvas.create_line(
            x1, y1, x2, y2,
            fill=LINE_COLOR,
            width=LINE_WIDTH,
            capstyle=tk.ROUND
        )
    
    def update(self):
        try:
            # Overlay transparent machen für Screenshot (kein Blinken!)
            self.root.attributes("-alpha", 0)
            self.root.update_idletasks()
            
            # Screenshot
            img = self.capture_screen()
            
            # Overlay wieder sichtbar
            self.root.attributes("-alpha", 1)
            
            # Linie erkennen
            line = LineDetector.detect(img)
            
            if line:
                x1, y1, x2, y2 = line
                # Linie in beide Richtungen verlängern
                ex1, ey1, ex2, ey2 = self.extend_line_full(x1, y1, x2, y2)
                # Zeichnen
                self.draw_line(ex1, ey1, ex2, ey2)
            else:
                self.canvas.delete("all")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        self.root.after(SCAN_INTERVAL_MS, self.update)
    
    def quit(self):
        print("👋 Closing overlay...")
        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        self.root.mainloop()


def main():
    print("=" * 50)
    print("  🎱 8 Ball Pool Trajectory Overlay")
    print("=" * 50)
    print()
    
    overlay = TrajectoryOverlay()
    overlay.run()


if __name__ == "__main__":
    main()
