import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageOps
import io
import os
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PDF 視覺化貼圖系統", layout="wide")

st.title("📄 PDF 視覺化貼圖 - 按鈕切換版")

# --- 初始化 Session State ---
if 'points' not in st.session_state:
    st.session_state.points = []
if 'current_logo' not in st.session_state:
    st.session_state.current_logo = "logo1.png"

with st.sidebar:
    st.header("1. 工具選單")
    uploaded_file = st.file_uploader("上傳 PDF 檔案", type=["pdf"])
    
    st.write("---")
    st.write("2. 選擇 Logo (按鈕切換):")
    
    # 建立五個按鈕來切換 Logo
    # 使用 columns 讓按鈕排版更漂亮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Logo 1"): st.session_state.current_logo = "logo1.png"
        if st.button("Logo 3"): st.session_state.current_logo = "logo3.png"
        if st.button("Logo 5"): st.session_state.current_logo = "logo5.png"
    with col2:
        if st.button("Logo 2"): st.session_state.current_logo = "logo2.png"
        if st.button("Logo 4"): st.session_state.current_logo = "logo4.png"

    st.info(f"🎯 目前選中: **{st.session_state.current_logo}**")
    
    # 顯示目前選中的 Logo 小圖預覽
    if os.path.exists(st.session_state.current_logo):
        st.image(st.session_state.current_logo, width=80)
    
    st.write("---")
    if st.button("清除選點 / 重新標註", use_container_width=True):
        st.session_state.points = []
        st.rerun()

# --- 主要操作區 ---
if uploaded_file:
    pdf_data = uploaded_file.read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    page = doc[0]
    
    # 轉成預覽圖並加上邊界
    zoom = 1.5
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    raw_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # 增加深灰色文件邊界感 (2px)
    offset = 2
    bg_with_border = ImageOps.expand(raw_img, border=offset, fill='#7f8c8d')
    
    display_img = bg_with_border.copy()
    draw = ImageDraw.Draw(display_img, "RGBA")
    
    # 繪製選點與預覽框
    if len(st.session_state.points) >= 1:
        p1 = st.session_state.points[0]
        draw.ellipse((p1[0]-4, p1[1]-4, p1[0]+4, p1[1]+4), fill="#e74c3c")
        
    if len(st.session_state.points) == 2:
        p1, p2 = st.session_state.points
        x0, y0 = min(p1[0], p2[0]), min(p1[1], p2[1])
        x1, y1 = max(p1[0], p2[0]), max(p1[1], p2[1])
        
        # 繪製橘色預覽邊框
        draw.rectangle([x0, y0, x1, y1], outline="#fb8c00", width=3, fill=(251, 140, 0, 40))
        
        # 繪製 Logo 預覽
        try:
            w, h = int(x1 - x0), int(y1 - y0)
            if w > 5 and h > 5:
                logo = Image.open(st.session_state.current_logo).convert("RGBA")
                logo_resized = logo.resize((w, h), Image.Resampling.LANCZOS)
                display_img.paste(logo_resized, (int(x0), int(y0)), logo_resized)
        except:
            pass

    st.subheader("請點擊圖面「兩次」決定位置。橘色方框為預覽範圍。")
    
    # 獲取座標
    coords = streamlit_image_coordinates(display_img, key="pdf_preview")

    if coords:
        new_point = (coords["x"], coords["y"])
        if not st.session_state.points or st.session_state.points[-1] != new_point:
            st.session_state.points.append(new_point)
            if len(st.session_state.points) > 2:
                st.session_state.points = st.session_state.points[-2:]
            st.rerun()

    # 存檔按鈕 (按鈕 7)
    if len(st.session_state.points) == 2:
        st.write("---")
        if st.button("按鈕 7: 存成 PDF 檔並下載", type="primary", use_container_width=True):
            p1, p2 = st.session_state.points
            pdf_x0 = (min(p1[0], p2[0]) - offset) / zoom
            pdf_y0 = (min(p1[1], p2[1]) - offset) / zoom
            pdf_x1 = (max(p1[0], p2[0]) - offset) / zoom
            pdf_y1 = (max(p1[1], p2[1]) - offset) / zoom
            
            page.insert_image(fitz.Rect(pdf_x0, pdf_y0, pdf_x1, pdf_y1), filename=st.session_state.current_logo)
            
            out_pdf = io.BytesIO()
            doc.save(out_pdf)
            st.download_button("📥 點我下載成品 PDF", out_pdf.getvalue(), "output.pdf", "application/pdf")
else:
    st.info("👈 請先從左側上傳 PDF 檔案開始操作。")
