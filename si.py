import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

class UltimatePDFEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 視覺化貼圖系統 - 最終版")
        self.root.geometry("1200x900")
        self.root.configure(bg="#f0f0f0")

        # 核心數據
        self.pdf_doc = None
        self.current_logo_path = "logo1.png"
        self.logo_raw = None
        self.preview_tk_img = None
        self.logo_preview_id = None
        
        self.start_x, self.start_y = 0, 0
        self.end_x, self.end_y = 0, 0
        self.scale_factor = 1.0

        # --- 介面佈局 ---
        # 左側控制台
        self.sidebar = tk.Frame(root, width=250, bg="#34495e", padx=20)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(self.sidebar, text="PDF 貼圖系統", fg="white", bg="#34495e", font=("Arial", 16, "bold")).pack(pady=30)

        # 按鈕 1
        tk.Button(self.sidebar, text="1. 匯入檔案", command=self.import_file, height=2, width=20, bg="#ecf0f1").pack(pady=10)

        tk.Label(self.sidebar, text="選擇 Logo 圖片:", fg="#bdc3c7", bg="#34495e").pack(pady=(20, 5))
        
        # 按鈕 2 ~ 6
        logo_list = [("logo1.png", "按鈕 2: Logo 1"), ("logo2.png", "按鈕 3: Logo 2"), 
                     ("logo3.png", "按鈕 4: Logo 3"), ("logo4.png", "按鈕 5: Logo 4"), 
                     ("logo5.png", "按鈕 6: Logo 5")]
        
        for path, name in logo_list:
            btn = tk.Button(self.sidebar, text=name, command=lambda p=path: self.load_logo(p), width=20)
            btn.pack(pady=2)

        # 按鈕 7
        self.btn_save = tk.Button(self.sidebar, text="7. 存成 PDF 檔", command=self.save_pdf, 
                                  bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), 
                                  width=20, height=2, state=tk.DISABLED)
        self.btn_save.pack(side=tk.BOTTOM, pady=40)

        # 右側預覽區
        self.view_area = tk.Frame(root, bg="#95a5a6")
        self.view_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.view_area, bg="white", highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # 滑鼠事件
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.load_logo("logo1.png")

    def load_logo(self, path):
        if os.path.exists(path):
            self.current_logo_path = path
            self.logo_raw = Image.open(path).convert("RGBA")
            self.root.title(f"目前準備貼入：{path}")
        else:
            messagebox.showwarning("找不到檔案", f"請確認 {path} 是否在資料夾中")

    def import_file(self):
        f_path = filedialog.askopenfilename(filetypes=[("PDF 檔案", "*.pdf")])
        if not f_path: return
        try:
            self.pdf_doc = fitz.open(f_path)
            self.render_pdf()
            self.btn_save.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    def render_pdf(self):
        page = self.pdf_doc[0]
        # 計算縮放以適應螢幕
        screen_h = 800
        self.scale_factor = screen_h / page.rect.height
        
        pix = page.get_pixmap(matrix=fitz.Matrix(self.scale_factor, self.scale_factor))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.preview_tk_img = ImageTk.PhotoImage(img)
        
        self.canvas.config(width=pix.width, height=pix.height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_tk_img)

    def on_click(self, event):
        self.start_x, self.start_y = event.x, event.y

    def on_drag(self, event):
        if not self.logo_raw or not self.pdf_doc: return
        
        w = abs(event.x - self.start_x)
        h = abs(event.y - self.start_y)
        if w < 5 or h < 5: return

        # --- 即時預覽 Logo ---
        resized = self.logo_raw.resize((w, h), Image.Resampling.LANCZOS)
        self.tk_logo_live = ImageTk.PhotoImage(resized)
        
        if self.logo_preview_id:
            self.canvas.delete(self.logo_preview_id)
        
        # 取得左上角點 (支援往回拉)
        x0, y0 = min(self.start_x, event.x), min(self.start_y, event.y)
        self.logo_preview_id = self.canvas.create_image(x0, y0, anchor=tk.NW, image=self.tk_logo_live)

    def on_release(self, event):
        self.end_x, self.end_y = event.x, event.y

    def save_pdf(self):
        out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not out_path: return

        try:
            # 換算回 PDF 真實座標
            x0 = min(self.start_x, self.end_x) / self.scale_factor
            y0 = min(self.start_y, self.end_y) / self.scale_factor
            x1 = max(self.start_x, self.end_x) / self.scale_factor
            y1 = max(self.start_y, self.end_y) / self.scale_factor
            
            page = self.pdf_doc[0]
            page.insert_image(fitz.Rect(x0, y0, x1, y1), filename=self.current_logo_path)
            self.pdf_doc.save(out_path)
            messagebox.showinfo("成功", "成品 PDF 已儲存！")
        except Exception as e:
            messagebox.showerror("失敗", str(e))

if __name__ == "__main__":
    # 修正 Windows 縮放導致模糊的問題
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    root = tk.Tk()
    app = UltimatePDFEditor(root)
    root.mainloop()
