import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageOps  # 導入 ImageOps 處理邊框
import io
import os
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PDF 視覺化貼圖系統", layout="wide")

st.title("📄 PDF 視覺化貼圖 - 邊界增強版")

# 初始化點擊紀錄
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
    
    st.info("💡 提示：點擊圖面「兩次」決定位置。橘色方框為預覽範圍。")

if uploaded_file:
    # 1. 讀取 PDF
    pdf_data = uploaded_file.read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    page = doc[0]
    
    # 2. 轉成預覽圖
    zoom = 1.5
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    raw_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # --- 3. 增加文件邊界感 (加上灰色外邊框) ---
    # 為原始圖增加 2 像素的深灰色邊框，模擬紙張邊緣
    bg_with_border = ImageOps.expand(raw_img, border=2, fill='#7f8c8d')
    
    display_img = bg_with_border.copy()
    draw = ImageDraw.Draw(display_img, "RGBA")
    
    # 補償邊框產生的偏移 (選點座標會因為邊框多出 2 像素)
    offset = 2

    # --- 4. 繪製標示框與 Logo ---
    if len(st.session_state.points) >= 1:
        # 標示第一點
        p1 = st.session_state.points[0]
        r = 4
        draw.ellipse((p1[0]-r, p1[1]-r, p1[0]+r, p1[1]+r), fill="#e74c3c")
        
    if len(st.session_state.points) == 2:
        p1, p2 = st.session_state.points
        x0, y0 = min(p1[0], p2[0]), min(p1[1], p2[1])
        x1, y1 = max(p1[0], p2[0]), max(p1[1], p2[1])
        
        # 畫出橘色虛線感外框與半透明填充
        draw.rectangle([x0, y0, x1, y1], outline="#fb8c00", width=3, fill=(251, 140, 0, 40))
        
        # 貼入 Logo 預覽
        try:
            w, h = int(x1 - x0), int(y1 - y0)
            if w > 5 and h > 5:
                logo = Image.open(logo_option).convert("RGBA")
                logo_resized = logo.resize((w, h), Image.Resampling.LANCZOS)
                display_img.paste(logo_resized, (int(x0), int(y0)), logo_resized)
        except:
            pass

    # 5. 顯示圖片並偵測點擊
    st.subheader("文件操作區 (橘框標示 Logo 範圍)")
    coords = streamlit_image_coordinates(display_img, key="pdf_preview")

    if coords:
        new_point = (coords["x"], coords["y"])
        if not st.session_state.points or st.session_state.points[-1] != new_point:
            st.session_state.points.append(new_point)
            if len(st.session_state.points) > 2:
                st.session_state.points = st.session_state.points[-2:]
            st.rerun()

    # 6. 存檔匯出
    if len(st.session_state.points) == 2:
        if st.button("7. 存成 PDF 檔"):
            p1, p2 = st.session_state.points
            # 注意：存入 PDF 時要扣除邊框 offset，並除以 zoom 還原座標
            pdf_x0 = (min(p1[0], p2[0]) - offset) / zoom
            pdf_y0 = (min(p1[1], p2[1]) - offset) / zoom
            pdf_x1 = (max(p1[0], p2[0]) - offset) / zoom
            pdf_y1 = (max(p1[1], p2[1]) - offset) / zoom
            
            page.insert_image(fitz.Rect(pdf_x0, pdf_y0, pdf_x1, pdf_y1), filename=logo_option)
            
            out_pdf = io.BytesIO()
            doc.save(out_pdf)
            st.download_button("📥 點我下載成品 PDF", out_pdf.getvalue(), "output.pdf", "application/pdf")
else:
    st.info("👈 請從左側選單上傳檔案以開始操作。")
