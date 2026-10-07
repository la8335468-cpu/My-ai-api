import io
import os
import gc
import requests
from flask import Flask, request, send_file
from PIL import Image
from rembg import remove, new_session

app = Flask(__name__)

# 1. Sabse halka AI model (Render ki 512MB RAM ke liye safe)
session = new_session("u2netp")

# 2. Warm-up: Server start hote hi model ready ho jaye (First request timeout na ho)
try:
    dummy_img = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
    remove(dummy_img, session=session)
    del dummy_img
    gc.collect()
except Exception as e:
    print(f"Warmup warning: {e}")

@app.route('/', methods=['GET'])
def home():
    return "AI Background Server is Live & Running!"

@app.route('/v1.0/removebg', methods=['POST'])
def process_bg():
    try:
        # Step A: App se aayi photo read karein
        input_data = request.data
        if not input_data:
            return "No image data received", 400

        person_img = Image.open(io.BytesIO(input_data)).convert("RGBA")
        
        # RAM crash (502) se bachne ke liye image 320x320 resize karein
        person_img.thumbnail((320, 320))

        # Step B: Original photo ka background remove karein
        person_cutout = remove(person_img, session=session)

        # Step C: Pollinations AI se Garden background download karein
        bg_url = "https://image.pollinations.ai/prompt/green%20garden?width=320&height=320&nologo=true"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            bg_resp = requests.get(bg_url, headers=headers, timeout=20)
            if bg_resp.status_code == 200:
                bg_img = Image.open(io.BytesIO(bg_resp.content)).convert("RGBA")
            else:
                bg_img = Image.new("RGBA", person_cutout.size, (255, 255, 255, 255))
        except Exception:
            # Agar Pollinations connect na ho toh white background lagayein
            bg_img = Image.new("RGBA", person_cutout.size, (255, 255, 255, 255))

        # Step D: Background par aadmi ka cutout merge karein
        bg_img = bg_img.resize(person_cutout.size)
        bg_img.paste(person_cutout, (0, 0), mask=person_cutout)

        # Step E: Final JPEG file ready karein
        output = io.BytesIO()
        bg_img.convert("RGB").save(output, format="JPEG", quality=80)
        output.seek(0)

        # RAM ko turant free karein taaki server kill na ho
        del person_img
        del person_cutout
        del bg_img
        gc.collect()

        return send_file(output, mimetype="image/jpeg")

    except Exception as e:
        return f"Server Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
