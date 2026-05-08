import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageOps
import io
import os
import subprocess
import tempfile
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="通用檔案貼圖系統", layout="wide")

st.title("📄 跨格式標註系統 (PDF/DOCX/XLSX)")

# --- 初始化 Session State ---
if 'points' not in st.session_state:
    st.session_state.points = []
if 'current_logo' not in st.session_state:
    st.session_state.current_logo = "logo1.png"
if 'pdf_doc' not in st.session_state:
    st.session_state.pdf_doc = None

# --- 核心轉檔函數 ---
def convert_to_pdf(uploaded_file):
    """將上傳的檔案轉換為 PDF 格式"""
    ext = uploaded_file.name.split(".")[-1].lower()
    
    # 建立臨時目錄處理檔案
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if ext == "pdf":
            return fitz.open(input_path).tobytes()
        
        # 使用 LibreOffice 進行無介面轉換 (Headless Mode)
        try:
            # 這是 Linux 環境下的標準指令
            process = subprocess.run([
                'lowriter', '--headless', '--convert-to', 'pdf', 
                '--outdir', temp_dir, input_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 尋找產出的 PDF 檔案
            pdf_file_name = uploaded_file.name.rsplit(".", 1)[0] + ".pdf"
            output_pdf_path = os.path.join(temp_dir, pdf_file_name)
            
            if os.path.exists(output_pdf_path):
                with open(output_pdf_path, "rb") as f:
                    return f.read()
            else:
                st.error("轉檔失敗：找不到生成的 PDF。請檢查檔案內容。")
                return None
        except Exception as e:
            st.error(f"系統轉換錯誤: {e}\n(請確認 packages.txt 已包含 libreoffice)")
            return None

# --- 側邊欄 ---
with st.sidebar:
    st.header("1. 檔案上傳")
    file = st.file_uploader("支援 PDF, DOC, DOCX, XLS, XLSX", type=["pdf", "doc", "docx", "xls", "xlsx"])
    
    if file:
        if st.button("🔄 執行/重新轉檔預覽"):
            with st.spinner("正在轉換檔案格式，請稍候..."):
                pdf_bytes = convert_to_pdf(file)
                if pdf_bytes:
                    st.session_state.pdf_doc = pdf_bytes
                    st.session_state.points = [] # 重置座標
                    st.success("✅ 轉檔完成！")

    st.write("---")
    st.write("2. 選擇 Logo:")
    cols = st.columns(2)
    for i in range(1, 6):
        l_path = f"logo{i}.png"
        with cols[(i-1)%2]:
            if st.button(f"Logo {i}", use_container_width=True):
                st.session_state.current_logo = l_path
    
    st.info(f"🎯 目標: **{st.session_state.current_logo}**")
    if st.button("🗑️ 清除選點", use_container_width=True):
        st.session_state.points = []
        st.rerun()

# --- 主要操作區 ---
if st.session_state.pdf_doc:
    # 開啟 PDF 位元組
    doc = fitz.open(stream=st.session_state.pdf_doc, filetype="pdf")
    page = doc[0] # 預設處理第一頁
    
    # 預覽圖製作
    zoom = 1.5
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    raw_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # 增加邊界感
    offset = 2
    bg_with_border = ImageOps.expand(raw_img, border=offset, fill='#7f8c8d')
    display_img = bg_with_border.copy()
    draw = ImageDraw.Draw(display_img, "RGBA")
    
    # 標註邏輯
    if len(st.session_state.points) >= 1:
        p1 = st.session_state.points[0]
        draw.ellipse((p1[0]-4, p1[1]-4, p1[0]+4, p1[1]+4), fill="red")
        
    if len(st.session_state.points) == 2:
        p1, p2 = st.session_state.points
        x0, y0, x1, y1 = min(p1[0], p2[0]), min(p1[1], p2[1]), max(p1[0], p2[0]), max(p1[1], p2[1])
        draw.rectangle([x0, y0, x1, y1], outline="#fb8c00", width=3, fill=(251, 140, 0, 40))
        
        # 貼圖預覽
        try:
            w, h = int(x1 - x0), int(y1 - y0)
            logo = Image.open(st.session_state.current_logo).convert("RGBA")
            logo_resized = logo.resize((w, h), Image.Resampling.LANCZOS)
            display_img.paste(logo_resized, (int(x0), int(y0)), logo_resized)
        except: pass

    st.subheader("請在下方預覽圖點擊兩次以標註位置")
    coords = streamlit_image_coordinates(display_img, key="main_editor")

    if coords:
        new_point = (coords["x"], coords["y"])
        if not st.session_state.points or st.session_state.points[-1] != new_point:
            st.session_state.points.append(new_point)
            if len(st.session_state.points) > 2:
                st.session_state.points = st.session_state.points[-2:]
            st.rerun()

    # 下載按鈕
    if len(st.session_state.points) == 2:
        if st.button("🚀 7. 生成並下載最終 PDF", type="primary", use_container_width=True):
            p1, p2 = st.session_state.points
            rect = fitz.Rect(
                (min(p1[0], p2[0])-offset)/zoom, (min(p1[1], p2[1])-offset)/zoom,
                (max(p1[0], p2[0])-offset)/zoom, (max(p1[1], p2[1])-offset)/zoom
            )
            page.insert_image(rect, filename=st.session_state.current_logo)
            output = io.BytesIO()
            doc.save(output)
            st.download_button("📥 下載成品 PDF", output.getvalue(), "annotated.pdf")
else:
    st.info("👈 請上傳檔案並點擊「執行轉檔預覽」按鈕。")
