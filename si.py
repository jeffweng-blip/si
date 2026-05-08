import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageOps
import io
import os
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="多功能檔案貼圖系統", layout="wide")

st.title("📄 多功能貼圖系統 (支援 PDF/Word/Excel)")

# --- 初始化 Session State ---
if 'points' not in st.session_state:
    st.session_state.points = []
if 'current_logo' not in st.session_state:
    st.session_state.current_logo = "logo1.png"

with st.sidebar:
    st.header("1. 工具選單")
    # 增加支援格式
    uploaded_file = st.file_uploader("上傳檔案", type=["pdf", "doc", "docx", "xls", "xlsx"])
    
    st.write("---")
    st.write("2. 選擇 Logo:")
    cols = st.columns(2)
    for i in range(1, 6):
        l_path = f"logo{i}.png"
        with cols[(i-1)%2]:
            if st.button(f"Logo {i}"):
                st.session_state.current_logo = l_path
                
    st.info(f"🎯 選中: **{st.session_state.current_logo}**")
    if os.path.exists(st.session_state.current_logo):
        st.image(st.session_state.current_logo, width=60)
    
    st.write("---")
    if st.button("清除標註", use_container_width=True):
        st.session_state.points = []
        st.rerun()

# --- 檔案處理邏輯 ---
def get_pdf_doc(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()
    
    if ext == "pdf":
        return fitz.open(stream=uploaded_file.read(), filetype="pdf")
    
    elif ext in ["docx", "doc"]:
        st.warning("⚠️ Word 預覽需先轉換為 PDF。建議手動轉 PDF 後上傳以獲得最佳效果。")
        # 這裡僅能示範邏輯，雲端環境轉換 docx 需預裝 LibreOffice
        return None 

    elif ext in ["xlsx", "xls"]:
        # Excel 處理：將表格轉為圖片 PDF
        df = pd.read_excel(uploaded_file)
        # 簡單呈現前 20 列作為預覽
        st.write("Excel 內容預覽 (前20列):")
        st.dataframe(df.head(20))
        # Excel 貼圖通常建議針對導出的 PDF 進行，此處功能受限
        return None
    return None

if uploaded_file:
    doc = get_pdf_doc(uploaded_file)
    
    if doc:
        page = doc[0]
        zoom = 1.5
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        raw_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        offset = 2
        bg_with_border = ImageOps.expand(raw_img, border=offset, fill='#7f8c8d')
        display_img = bg_with_border.copy()
        draw = ImageDraw.Draw(display_img, "RGBA")
        
        # 繪製邏輯
        if len(st.session_state.points) >= 1:
            p1 = st.session_state.points[0]
            draw.ellipse((p1[0]-4, p1[1]-4, p1[0]+4, p1[1]+4), fill="#e74c3c")
            
        if len(st.session_state.points) == 2:
            p1, p2 = st.session_state.points
            x0, y0 = min(p1[0], p2[0]), min(p1[1], p2[1])
            x1, y1 = max(p1[0], p2[0]), max(p1[1], p2[1])
            draw.rectangle([x0, y0, x1, y1], outline="#fb8c00", width=3, fill=(251, 140, 0, 40))
            
            try:
                w, h = int(x1 - x0), int(y1 - y0)
                logo = Image.open(st.session_state.current_logo).convert("RGBA")
                logo_resized = logo.resize((w, h), Image.Resampling.LANCZOS)
                display_img.paste(logo_resized, (int(x0), int(y0)), logo_resized)
            except: pass

        st.subheader("請點選兩次決定貼圖位置")
        coords = streamlit_image_coordinates(display_img, key="doc_preview")

        if coords:
            new_point = (coords["x"], coords["y"])
            if not st.session_state.points or st.session_state.points[-1] != new_point:
                st.session_state.points.append(new_point)
                if len(st.session_state.points) > 2:
                    st.session_state.points = st.session_state.points[-2:]
                st.rerun()

        if len(st.session_state.points) == 2:
            if st.button("按鈕 7: 存成 PDF 檔", type="primary", use_container_width=True):
                p1, p2 = st.session_state.points
                pdf_x0 = (min(p1[0], p2[0]) - offset) / zoom
                pdf_y0 = (min(p1[1], p2[1]) - offset) / zoom
                pdf_x1 = (max(p1[0], p2[0]) - offset) / zoom
                pdf_y1 = (max(p1[1], p2[1]) - offset) / zoom
                
                page.insert_image(fitz.Rect(pdf_x0, pdf_y0, pdf_x1, pdf_y1), filename=st.session_state.current_logo)
                out_pdf = io.BytesIO()
                doc.save(out_pdf)
                st.download_button("📥 下載成品 PDF", out_pdf.getvalue(), "output.pdf", "application/pdf")
    else:
        st.warning("目前 Word/Excel 預覽功能在 Web 環境受限。為了保證貼圖精準，建議將 Word/Excel 另存為 PDF 後再上傳。")
else:
    st.info("👈 請上傳檔案 (PDF 效果最佳)")
