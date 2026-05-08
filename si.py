import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import os
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PDF 視覺化貼圖系統", layout="wide")

st.title("📄 PDF 視覺化貼圖 - 即時預覽版")

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
    
    st.info("💡 操作說明：\n1. 在圖上點第一下 (左上)\n2. 在圖上點第二下 (右下)\n3. 畫面會出現預覽，滿意後按儲存。")

if uploaded_file:
    # 讀取 PDF
    pdf_data = uploaded_file.read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    page = doc[0]
    
    # 轉成圖片供預覽與點擊 (zoom=1.5 確保清晰度)
    zoom = 1.5
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    bg_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # --- 核心預覽邏輯 ---
    display_img = bg_img.copy()
    
    # 如果已經點了兩點，先在 display_img 上合成 Logo 供預覽
    if len(st.session_state.points) == 2:
        try:
            p1, p2 = st.session_state.points
            x0, y0 = min(p1[0], p2[0]), min(p1[1], p2[1])
            x1, y1 = max(p1[0], p2[0]), max(p1[1], p2[1])
            width, height = int(x1 - x0), int(y1 - y0)
            
            if width > 5 and height > 5:
                # 讀取 Logo 並縮放至點選的大小
                logo = Image.open(logo_option).convert("RGBA")
                logo_resized = logo.resize((width, height), Image.Resampling.LANCZOS)
                
                # 合成預覽圖 (在網頁顯示層)
                display_img.paste(logo_resized, (int(x0), int(y0)), logo_resized)
        except Exception as e:
            st.error(f"預覽生成失敗: {e}")

    # 顯示圖片並捕捉點擊
    st.subheader("點擊圖面決定位置")
    coords = streamlit_image_coordinates(display_img, key="pdf_preview")

    if coords:
        new_point = (coords["x"], coords["y"])
        if not st.session_state.points or st.session_state.points[-1] != new_point:
            st.session_state.points.append(new_point)
            if len(st.session_state.points) > 2:
                st.session_state.points = st.session_state.points[-2:]
            st.rerun() # 點擊後重新整理以顯示預覽

    # 存檔按鈕
    if len(st.session_state.points) == 2:
        st.success("✅ 預覽已生成，若位置正確請按下方按鈕存檔。")
        if st.button("7. 存成 PDF 檔並下載"):
            try:
                p1, p2 = st.session_state.points
                x0, y0 = min(p1[0], p2[0]) / zoom, min(p1[1], p2[1]) / zoom
                x1, y1 = max(p1[0], p2[0]) / zoom, max(p1[1], p2[1]) / zoom
                
                rect = fitz.Rect(x0, y0, x1, y1)
                page.insert_image(rect, filename=logo_option)
                
                output_pdf = io.BytesIO()
                doc.save(output_pdf)
                
                st.download_button(
                    label="📥 下載成品 PDF",
                    data=output_pdf.getvalue(),
                    file_name="finished_document.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"存檔出錯: {e}")
else:
    st.info("👈 請先從側邊欄上傳 PDF 檔案。")
