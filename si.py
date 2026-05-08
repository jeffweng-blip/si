import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import os
from streamlit_drawable_canvas import st_canvas

# 設定網頁標題與版面
st.set_page_config(page_title="PDF 多功能貼圖系統", layout="wide")

st.title("📄 PDF 貼圖系統 (Streamlit 穩定版)")

# --- 側邊欄：控制面板 ---
with st.sidebar:
    st.header("1. 工具選單")
    
    # 匯入檔案
    uploaded_file = st.file_uploader("上傳 PDF 檔案", type=["pdf"])
    
    st.write("---")
    st.write("2. 選擇貼圖 Logo:")
    
    # Logo 選擇按鈕 (對應按鈕 2~6)
    logo_option = st.selectbox(
        "切換 Logo 檔案",
        ["logo1.png", "logo2.png", "logo3.png", "logo4.png", "logo5.png"]
    )
    
    # 顯示目前選中的 Logo 預覽
    if os.path.exists(logo_option):
        logo_img = Image.open(logo_option)
        st.image(logo_img, caption=f"目前選中: {logo_option}", width=100)
    else:
        st.error(f"找不到 {logo_option}，請確認檔案與 si.py 在同一資料夾")

# --- 主要區域 ---
if uploaded_file:
    # 讀取 PDF 並轉換第一頁為預覽圖
    pdf_data = uploaded_file.read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    page = doc[0]
    
    # 為了讓畫布與 PDF 座標對齊，固定一個縮放倍率
    zoom = 1.5
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    bg_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    st.subheader("3. 在下方區域拖曳出 Logo 的位置與大小")
    st.info("💡 操作說明：在圖面上點擊並拖曳出一個「橘色方框」，該框就是 Logo 的位置。")

    # 建立容器讓圖片與畫布重疊 (解決 AttributeError 的穩定方案)
    # 我們將畫布設為透明，並透過 Streamlit 顯示
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # 橘色半透明
        stroke_width=2,
        stroke_color="#fb8c00",
        background_image=bg_img, # 如果這行報錯，請刪除這行並參考下方註解
        update_streamlit=True,
        height=bg_img.height,
        width=bg_img.width,
        drawing_mode="rect",
        key="pdf_canvas",
    )

    # 4. 存檔與下載 (按鈕 7)
    st.write("---")
    if st.button("7. 點我合成並準備存檔"):
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if len(objects) > 0:
                # 取得最後一個畫出的矩形
                rect_data = objects[-1]
                x = rect_data["left"]
                y = rect_data["top"]
                w = rect_data["width"]
                h = rect_data["height"]
                
                # 將網頁畫布座標換算回 PDF 點數座標 (除以 zoom)
                pdf_rect = fitz.Rect(x/zoom, y/zoom, (x+w)/zoom, (y+h)/zoom)
                
                try:
                    # 執行貼圖
                    page.insert_image(pdf_rect, filename=logo_option)
                    
                    # 儲存到記憶體
                    output_pdf = io.BytesIO()
                    doc.save(output_pdf)
                    
                    st.success(f"✅ 已成功將 {logo_option} 嵌入 PDF！")
                    st.download_button(
                        label="💾 點我下載成品 PDF",
                        data=output_pdf.getvalue(),
                        file_name="output_finished.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"儲存失敗：{e}")
            else:
                st.warning("您還沒在畫面上畫出框框喔！")

else:
    st.warning("👈 請先在左側上傳 PDF 檔案。")
