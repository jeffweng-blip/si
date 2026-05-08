import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import io
import os

st.set_page_config(page_title="PDF 視覺化貼圖", layout="wide")

st.title("📄 PDF 視覺化貼圖系統 (Streamlit 雲端版)")

# 初始化座標紀錄
if 'points' not in st.session_state:
    st.session_state.points = []

with st.sidebar:
    st.header("1. 工具選單")
    uploaded_file = st.file_uploader("上傳 PDF", type=["pdf"])
    
    st.write("---")
    logo_option = st.selectbox("選擇 Logo", ["logo1.png", "logo2.png", "logo3.png", "logo4.png", "logo5.png"])
    
    if st.button("清除選點"):
        st.session_state.points = []
        st.rerun()

if uploaded_file:
    # 讀取 PDF
    pdf_data = uploaded_file.read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    page = doc[0]
    
    # 轉成圖片供點擊
    zoom = 1.5
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    bg_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    st.subheader("2. 請在下方圖面上點擊「兩次」來決定 Logo 位置")
    st.caption("第一點：Logo 左上角 | 第二點：Logo 右下角")

    # 捕捉點擊座標
    # 使用 streamlit 原生的標註功能
    from streamlit_image_coordinates import streamlit_image_coordinates
    
    # 這裡需要安裝 pip install streamlit-image-coordinates
    try:
        from streamlit_image_coordinates import streamlit_image_coordinates
        value = streamlit_image_coordinates(bg_img, key="coords")
        
        if value:
            new_point = (value["x"], value["y"])
            if not st.session_state.points or st.session_state.points[-1] != new_point:
                st.session_state.points.append(new_point)
                if len(st.session_state.points) > 2:
                    st.session_state.points = st.session_state.points[-2:] # 只保留最後兩點
    except ImportError:
        st.error("請在 requirements.txt 加入 streamlit-image-coordinates")

    # 預覽邏輯
    if len(st.session_state.points) == 2:
        p1, p2 = st.session_state.points
        x0, y0 = min(p1[0], p2[0]), min(p1[1], p2[1])
        x1, y1 = max(p1[0], p2[0]), max(p1[1], p2[1])
        
        # 換算回 PDF 座標
        pdf_rect = fitz.Rect(x0/zoom, y0/zoom, x1/zoom, y1/zoom)
        
        # 顯示預覽
        st.success(f"已選定範圍：從 ({int(x0)}, {int(y0)}) 到 ({int(x1)}, {int(y1)})")
        
        if st.button("7. 存成 PDF 檔"):
            page.insert_image(pdf_rect, filename=logo_option)
            output_pdf = io.BytesIO()
            doc.save(output_pdf)
            st.download_button("📥 下載成品 PDF", output_pdf.getvalue(), "finished.pdf", "application/pdf")

else:
    st.info("👈 請先上傳 PDF")
