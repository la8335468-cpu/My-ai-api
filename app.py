import io
import requests
from flask import Flask, request, send_file
from PIL import Image
from rembg import remove, new_session

app = Flask(__name__)

# Lightweight model jo Render ki 512MB RAM me aaram se chale
session = new_session("u2netp")

@app.route('/v1.0/removebg', methods=['POST'])
def process_bg():
    try:
  
        input_data = request.data
        if not input_data:
            return "No image data received", 400

        person_img = Image.open(io.BytesIO(input_data)).convert("RGBA")

      
        person_cutout = remove(person_img, session=session)

  
        bg_url = "https://image.pollinations.ai/prompt/green%20garden?width=512&height=512&nologo=true"
        headers = {"User-Agent": "Mozilla/5.0"}
        bg_resp = requests.get(bg_url, headers=headers, timeout=15)
        
        if bg_resp.status_code == 200:
            bg_img = Image.open(io.BytesIO(bg_resp.content)).convert("RGBA")
        else:
            # Agar Pollinations fail ho to white canvas use karein
            bg_img = Image.new("RGBA", person_cutout.size, (255, 255, 255, 255))

  
        bg_img = bg_img.resize(person_cutout.size)
        bg_img.paste(person_cutout, (0, 0), mask=person_cutout)


        output = io.BytesIO()
        bg_img.convert("RGB").save(output, format="JPEG", quality=85)
        output.seek(0)
        return send_file(output, mimetype="image/jpeg")

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
