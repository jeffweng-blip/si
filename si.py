import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import os

st.set_page_config(page_title="PDF 貼圖系統 - 穩定版", layout="wide")

st.title("📄 PDF 貼圖系統 (100% 穩定版)")

with st.sidebar:
    st.header("1. 工具選單")
    uploaded_file = st.file_uploader("上傳 PDF 檔案", type=["pdf"])
    
    st.write("---")
    logo_option = st.selectbox("選擇 Logo", ["logo1.png", "logo2.png", "logo3.png", "logo4.png", "logo5.png"])
    
    if os.path.exists(logo_option):
        st.image(logo_option, caption=f"目前選中: {logo_option}", width=100)
    
    st.write("---")
    st.header("2. 設定位置與大小")
    # 讓使用者直接輸入座標與尺寸
    pdf_x = st.number_input("左邊距離 (X)", min_value=0, value=50)
    pdf_y = st.number_input("上方距離 (Y)", min_value=0, value=50)
    pdf_w = st.number_input("Logo 寬度", min_value=10, value=150)
    pdf_h = st.number_input("Logo 高度", min_value=10, value=150)

if uploaded_file:
    # 讀取 PDF 並預覽
    pdf_data = uploaded_file.read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    page = doc[0]
    
    # 預覽圖
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    bg_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    st.subheader("文件預覽")
    st.image(bg_img, use_container_width=True)

    # 按鈕 7：合成並存檔
    if st.button("7. 存成 PDF 檔"):
        try:
            # 使用輸入的座標
            # (x0, y0, x1, y1)
            rect = fitz.Rect(pdf_x, pdf_y, pdf_x + pdf_w, pdf_y + pdf_h)
            
            page.insert_image(rect, filename=logo_option)
            
            output_pdf = io.BytesIO()
            doc.save(output_pdf)
            
            st.success("✅ 貼圖成功！")
            st.download_button(
                label="📥 點我下載成品 PDF",
                data=output_pdf.getvalue(),
                file_name="finished.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"發生錯誤：{e}")
else:
    st.info("👈 請先從左側上傳 PDF。")
