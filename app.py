import os
import uuid
import random
from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp

# --- Konfigurácia ---
DOWNLOAD_FOLDER = 'downloads'

# Zoznam rôznych User-Agent stringov pre rotáciu, aby sme sa tvárili ako rôzne prehliadače
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0'
]

# --- Inicializácia aplikácie ---
app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

# Vytvorenie priečinka na sťahovanie, ak neexistuje
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# --- Hlavná logika aplikácie ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form.get('url', '').strip()
        custom_filename = request.form.get('filename')

        if not video_url:
            return "Chyba: Nebol zadaný žiadny odkaz na video."

        if custom_filename:
            if not custom_filename.lower().endswith('.mp4'):
                custom_filename += '.mp4'
            final_download_name = custom_filename
        else:
            final_download_name = 'stiahnute_video.mp4'

        temp_filename = f'video_temp_{uuid.uuid4()}.mp4'
        file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], temp_filename)

        # Funkcia na bezpečné vymazanie dočasného súboru po odoslaní
        @after_this_request
        def cleanup(response):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as error:
                    app.logger.error("Chyba pri mazaní súboru: %s", error)
            return response

        # Pokročilé nastavenia pre yt-dlp
        ydl_opts = {
            'format': 'best[height<=720][ext=mp4]/bestvideo[height<=720]+bestaudio/best',
            'outtmpl': file_path,
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'http_headers': {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept-Language': 'en-US,en;q=0.9,sk;q=0.8',
            },
            'retries': 3,
            'socket_timeout': 30,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Stiahnutie videa
                ydl.download([video_url])
                
                # Kontrola, či sa súbor naozaj vytvoril
                if not os.path.exists(file_path):
                    return "Chyba: Súbor sa nepodarilo vytvoriť na serveri."

            # Odoslanie súboru používateľovi
            return send_file(
                file_path,
                as_attachment=True,
                download_name=final_download_name
            )
        
        # Vylepšené spracovanie konkrétnych chýb
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if "429" in error_msg:
                return "Chyba: Príliš veľa požiadaviek. Server je dočasne zablokovaný. Skúste to znova o chvíľu."
            elif "Sign in to confirm" in error_msg:
                return "Chyba: Toto video vyžaduje overenie prihlásením. Skúste iné video."
            else:
                return f"Chyba pri sťahovaní: {error_msg}"
        except Exception as e:
            return f"Neočakávaná chyba: {str(e)}"

    # Zobrazenie hlavnej stránky pri prvej návšteve
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)