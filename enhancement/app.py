from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import os
import qrcode
import hashlib
import shutil

"""
Template from: https://github.com/alfanme/dts-deployment-ann
"""
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
app.config['UPLOAD_FOLDER'] = './static/images/'
app.secret_key = "f!#&^rty(*wjf(ijf)!#(*!t(h*!%(*&@)"
Session(app)

@app.route('/')
def index():
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    session["uid"] = hashlib.md5(bytes(ip, 'utf-8')).hexdigest()
    print(session.get("uid"))
    print(ip)
    return render_template('index.html')

@app.route('/homepage')
def process_user_transformation_choice():
    return render_template('image_video.html')

@app.route('/process_enhance_type', methods=["POST", "GET"])
def process_user_enhance_choice():
    enhance_type = request.form['enhance_type']
    return redirect(url_for(enhance_type))

@app.route('/enchancement')
def enchancement():
    return render_template("image_video.html")

@app.route('/photo')
def photo():
    return render_template("cf_photo_upload.html")

@app.route('/video')
def video():
    return render_template("esrgan_video_upload.html")

@app.route('/video_enhance_results')
def video_enhance_results():
    before_video = request.args.get('before_video')
    after_video = request.args.get('after_video')
    qr_path = request.args.get('qr_path')
    return render_template("video_enhanced_results.html", before_video=before_video, after_video=after_video, qr_path=qr_path)

@app.route('/media_upload', methods=["POST"])
def upload_video():
    if request.method == 'POST':
        target_dir = "./static/videos/user_upload"
        os.makedirs(target_dir, exist_ok=True) 
        media = request.files.get('video')
        filename = "results.mp4"
        new_filename = f"enhanced_{filename}"

        file_path = os.path.join(target_dir, filename)
        media.save(file_path)

        vid_type = request.form.get('media_type')

        if vid_type == "real":
            command = f'python es_setup.py {filename}'
            os.system(command)

    before_video = os.path.join("./static/videos/user_upload", filename)
    after_video = os.path.join("./static/videos/results", new_filename)
    qr_path = generate_qr_code(after_video)
    return redirect(url_for('video_enhance_results', before_video=before_video, after_video=after_video, qr_path=qr_path))

@app.route('/photo_upload', methods=["POST"])
def upload_gfpgan():
    if request.method == 'POST':
        target_dir = "./static/images/user_upload"
        os.makedirs(target_dir, exist_ok=True) 
        computing_device = request.form.get('computing-device')
        print("Computing Device: ", computing_device)
        file = request.files.get('image')
        filename = "source.png"
        file_path = os.path.join(target_dir, filename)
        file.save(file_path)

        CODEFORMER_FIDELITY = 0.9
        BACKGROUND_ENHANCE = True
        FACE_UPSAMPLE = True
        
        if BACKGROUND_ENHANCE:
            if FACE_UPSAMPLE:
                command = f"python inference_codeformer.py -w {CODEFORMER_FIDELITY} --input_path ./static/images/user_upload --bg_upsampler realesrgan --face_upsample --computing_device {computing_device}"
            else:
                command = f"python inference_codeformer.py -w {CODEFORMER_FIDELITY} --input_path ./static/images/user_upload --bg_upsampler realesrgan --computing_device {computing_device}"
        else:
            command = f"python inference_codeformer.py -w {CODEFORMER_FIDELITY} --input_path ./static/images/user_upload --computing_device {computing_device}"

        os.system(command)

        before_img = os.path.join("./static/images/user_upload", filename)
        restored_img = os.path.join("./static/images/results/user_upload_0.9/final_results", filename)

        qr_path = generate_qr_code(restored_img)

        return redirect(url_for('gfpgan_results', before_img=before_img, restored_img=restored_img, qr_path=qr_path))

@app.route('/gfpgan_results')
def gfpgan_results():
    before_img = request.args.get('before_img')
    restored_img = request.args.get('restored_img')
    qr_path = request.args.get('qr_path')
    return render_template("gfpgan_results.html", before_img=before_img, restored_img=restored_img, qr_path=qr_path)

def generate_qr_code(image_path):
    qr_directory = "./static/images/results"
    os.makedirs(qr_directory, exist_ok=True)  

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4)
    qr.add_data(request.url_root + image_path)
    qr.make(fit=True)
    qr_image = qr.make_image(fill='black', back_color='white')

    qr_path = os.path.join(qr_directory, "qr_gan_results.png")
    qr_image.save(qr_path)
    return qr_path

@app.route('/return_path', methods=['POST'])
def return_path():
    if request.method == 'POST':
        before_img_path = request.form.get('before_img_path')
        restored_img_path = request.form.get('restored_img_path')
        before_video_path = request.form.get('before_video_path')
        after_video_path = request.form.get('after_video_path')
        temp_folder = './static/videos/tmp_frames'
        temp_result = './results'
        if before_img_path is not None:
            os.remove(before_img_path)
        
        if restored_img_path is not None:
            os.remove(restored_img_path)
        
        if before_video_path is not None:
            os.remove(before_video_path)

        if after_video_path is not None:
            os.remove(after_video_path)

        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)

        if os.path.exists(temp_result):
            shutil.rmtree(temp_result)

    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
