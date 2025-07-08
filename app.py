import os
import uuid
from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp

DOWNLOAD_FOLDER = 'downloads'

app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form['url']
        custom_filename = request.form.get('filename')

        if custom_filename:
            if not custom_filename.lower().endswith('.mp4'):
                custom_filename += '.mp4'
            final_download_name = custom_filename
        else:
            final_download_name = 'stiahnute_video.mp4'

        temp_filename = f'video_temp_{uuid.uuid4()}.mp4'
        file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], temp_filename)

        @after_this_request
        def cleanup(response):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            try:
                os.remove(file_path)
            except Exception as error:
                app.logger.error("Chyba pri mazaní súboru: %s", error)
            return response

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': file_path,
            'merge_output_format': 'mp4',
            # TÁTO NOVÁ ČASŤ MASKUJE NAŠU APLIKÁCIU AKO PREHLIADAČ
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
            },
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            return send_file(
                file_path,
                as_attachment=True,
                download_name=final_download_name
            )
        except Exception as e:
            # Vrátime konkrétnu chybu od yt-dlp pre lepšiu diagnostiku
            return f"Nastala chyba: {e}"

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
