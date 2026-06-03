import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import base64
import io

st.title("Canvas Initial Drawing Test")
bg_image = Image.new("RGB", (300, 300), color="blue")
buffered = io.BytesIO()
bg_image.save(buffered, format="PNG")
img_str = base64.b64encode(buffered.getvalue()).decode()
data_url = f"data:image/png;base64,{img_str}"

initial_drawing = {
    "version": "4.4.0",
    "objects": [
        {
            "type": "image",
            "left": 0,
            "top": 0,
            "width": bg_image.width,
            "height": bg_image.height,
            "src": data_url,
            "selectable": False,
            "evented": False,
            "crossOrigin": None
        },
        {
            "type": "rect",
            "left": 50,
            "top": 50,
            "width": 100,
            "height": 100,
            "fill": "rgba(255, 0, 0, 0.5)",
            "selectable": True
        }
    ]
}

res = st_canvas(
    width=300,
    height=300,
    initial_drawing=initial_drawing,
    key="canvas_test_2"
)
if res.image_data is not None:
    st.write("Canvas ready")
