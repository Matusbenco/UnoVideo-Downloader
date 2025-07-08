import os
import uuid  # Import pre generovanie unikátnych názvov
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

        # VYTVORENIE UNIKÁTNEHO NÁZVU PRE DOČASNÝ SÚBOR
        temp_filename = f'video_temp_{uuid.uuid4()}.mp4'
        file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], temp_filename)

        @after_this_request
        def cleanup(response):
            # Pridanie hlavičiek, ktoré zabránia ukladaniu do cache prehliadača
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
            'outtmpl': file_path,  # Použije sa unikátny názov
            'merge_output_format': 'mp4',
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
            return f"Nastala chyba: {e}"

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)