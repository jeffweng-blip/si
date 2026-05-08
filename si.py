import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw  # 導入 ImageDraw 用於繪圖
import io
import os
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PDF 視覺化貼圖系統", layout="wide")

st.title("📄 PDF 視覺化貼圖 - 範圍標示版")

# 初始化紀錄點擊座標
if 'points' not in st.session_state:
    st.session_state.points = []

with st.sidebar:
    st.header("1. 工具選單")
    uploaded_file = st.file_uploader("上傳 PDF 檔案", type=["pdf"])
    
    st.write("---")
    logo_option = st.selectbox("選擇 Logo", ["logo1.png", "logo2.png", "logo3.png", "logo4.png", "logo5.png"])
    
    if st.button("清除選點 / 重新標註"):
        st.session_state.points = []
        st.rerun()

if uploaded_file:
    # 1. 讀取 PDF
    pdf_data = uploaded_file.read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    page = doc[0]
    
    # 2. 轉成預覽圖 (解析度縮放 1.5 倍)
    zoom = 1.5
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    bg_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # --- 3. 繪製標示框與預覽 Logo ---
    display_img = bg_img.copy()
    draw = ImageDraw.Draw(display_img, "RGBA") # 支援半透明顏色
    
    # 如果有點擊記錄，進行畫面標註
    if len(st.session_state.points) >= 1:
        # 標示第一點 (小紅點)
        p1 = st.session_state.points[0]
        r = 5
        draw.ellipse((p1[0]-r, p1[1]-r, p1[0]+r, p1[1]+r), fill="red")
        
    if len(st.session_state.points) == 2:
        # 標示矩形外框 (橘色半透明)
        p1, p2 = st.session_state.points
        x0, y0 = min(p1[0], p2[0]), min(p1[1], p2[1])
        x1, y1 = max(p1[0], p2[0]), max(p1[1], p2[1])
        
        # 畫出橘色外框與半透明填充
        draw.rectangle([x0, y0, x1, y1], outline="#fb8c00", width=3, fill=(251, 140, 0, 50))
        
        # 貼入 Logo 預覽
        try:
            width, height = int(x1 - x0), int(y1 - y0)
            if width > 5 and height > 5:
                logo = Image.open(logo_option).convert("RGBA")
                logo_resized = logo.resize((width, height), Image.Resampling.LANCZOS)
                display_img.paste(logo_resized, (int(x0), int(y0)), logo_resized)
        except:
            pass

    # 4. 顯示圖片並偵測點擊
    st.subheader("請點擊兩點決定範圍（自動顯示橘色外框）")
    coords = streamlit_image_coordinates(display_img, key="pdf_preview")

    if coords:
        new_point = (coords["x"], coords["y"])
        if not st.session_state.points or st.session_state.points[-1] != new_point:
            st.session_state.points.append(new_point)
            if len(st.session_state.points) > 2:
                st.session_state.points = st.session_state.points[-2:]
            st.rerun()

    # 5. 存檔功能
    if len(st.session_state.points) == 2:
        st.success("✅ 框選範圍已確認，請點擊下方按鈕匯出。")
        if st.button("7. 存成 PDF 檔"):
            p1, p2 = st.session_state.points
            # 座標還原回 PDF 的 Point 單位
            pdf_x0 = min(p1[0], p2[0]) / zoom
            pdf_y0 = min(p1[1], p2[1]) / zoom
            pdf_x1 = max(p1[0], p2[0]) / zoom
            pdf_y1 = max(p1[1], p2[1]) / zoom
            
            page.insert_image(fitz.Rect(pdf_x0, pdf_y0, pdf_x1, pdf_y1), filename=logo_option)
            
            out_pdf = io.BytesIO()
            doc.save(out_pdf)
            st.download_button("📥 下載成品 PDF", out_pdf.getvalue(), "output.pdf", "application/pdf")
else:
    st.info("👈 請先從側邊欄上傳檔案。")
