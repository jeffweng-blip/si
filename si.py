import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="PDF 多功能貼圖系統", layout="wide")

st.title("📄 PDF / Word 貼圖系統 (Streamlit版)")

# --- 側邊欄：控制面板 ---
with st.sidebar:
    st.header("工具選單")
    
    # 1. 匯入檔案
    uploaded_file = st.file_uploader("1. 匯入 PDF 檔案", type=["pdf"])
    
    st.write("---")
    st.write("選擇貼圖 Logo:")
    
    # 2-6. Logo 選擇
    logo_choice = st.radio(
        "選擇要貼入的 Logo",
        ["logo1.png", "logo2.png", "logo3.png", "logo4.png", "logo5.png"],
        index=0
    )
    
    try:
        logo_img = Image.open(logo_choice)
        st.image(logo_img, caption=f"目前選中: {logo_choice}", width=100)
    except:
        st.error(f"找不到 {logo_choice}，請確認檔案存在")

# --- 主要區域 ---
if uploaded_file:
    # 讀取 PDF
    pdf_data = uploaded_file.read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    page = doc[0]
    
    # 將 PDF 轉為圖片以便在網頁預覽
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    bg_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    st.subheader("2. 在下方圖面上拖曳出 Logo 的位置與大小")
    
    # 建立畫布供使用者拖曳矩形
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # 矩形填充顏色
        stroke_width=2,
        stroke_color="#e67e22",
        background_image=bg_img,
        update_streamlit=True,
        height=bg_img.height,
        width=bg_img.width,
        drawing_mode="rect",
        key="canvas",
    )

    # 3. 處理存檔 (按鈕 7)
    if st.button("7. 存成 PDF 檔"):
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if len(objects) > 0:
                # 取得最後一個畫出的矩形座標
                last_rect = objects[-1]
                x = last_rect["left"]
                y = last_rect["top"]
                w = last_rect["width"]
                h = last_rect["height"]
                
                # 換算回 PDF 座標
                # 因為預覽圖是 Matrix(1.5, 1.5)，所以要除以 1.5
                scale = 1.5
                pdf_rect = fitz.Rect(x/scale, y/scale, (x+w)/scale, (y+h)/scale)
                
                # 貼入圖片
                page.insert_image(pdf_rect, filename=logo_choice)
                
                # 輸出 PDF
                output_pdf = io.BytesIO()
                doc.save(output_pdf)
                
                st.success("🎉 貼圖完成！請點擊下方按鈕下載")
                st.download_button(
                    label="下載成品 PDF",
                    data=output_pdf.getvalue(),
                    file_name="finished_document.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("請先在圖面上畫出矩形框！")
else:
    st.info("請先從側邊欄上傳 PDF 檔案。")