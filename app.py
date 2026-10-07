import io
import requests
import gc
from flask import Flask, request, send_file
from PIL import Image
from rembg import remove, new_session

app = Flask(__name__)

# Ultra light model (sabse kam RAM lene wala)
session = new_session("u2netp")

@app.route('/v1.0/removebg', methods=['POST'])
def process_bg():
    try:
        input_data = request.data
        if not input_data:
            return "No data", 400

        # 1. Image open aur size turant chhota karein (RAM bachaane ke liye)
        person_img = Image.open(io.BytesIO(input_data)).convert("RGBA")
        person_img.thumbnail((320, 320))

        # 2. Background remove karein
        person_cutout = remove(person_img, session=session)

        # 3. Pollinations se garden background layein
        bg_url = "https://image.pollinations.ai/prompt/green%20garden?width=320&height=320&nologo=true"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        try:
            bg_resp = requests.get(bg_url, headers=headers, timeout=25)
            if bg_resp.status_code == 200:
                bg_img = Image.open(io.BytesIO(bg_resp.content)).convert("RGBA")
            else:
                bg_img = Image.new("RGBA", person_cutout.size, (255, 255, 255, 255))
        except Exception:
            bg_img = Image.new("RGBA", person_cutout.size, (255, 255, 255, 255))

        # 4. Canvas merge
        bg_img = bg_img.resize(person_cutout.size)
        bg_img.paste(person_cutout, (0, 0), mask=person_cutout)

        # 5. Output ready karein
        output = io.BytesIO()
        bg_img.convert("RGB").save(output, format="JPEG", quality=75)
        output.seek(0)

        # RAM saaf karein
        del person_img
        del person_cutout
        gc.collect()

        return send_file(output, mimetype="image/jpeg")

    except Exception as e:
        return f"Server Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
