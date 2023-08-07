from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session, jsonify, Response, make_response
from flask_session import Session
import os
import qrcode
import hashlib
import urllib.parse
import random
import shutil
from qiskit import QuantumCircuit, Aer, execute

"""
Template from: https://github.com/alfanme/dts-deployment-ann
"""
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
app.config['UPLOAD_FOLDER'] = './static/images/'
app.secret_key = "f!#&^rty(*wjf(ijf)!#(*!t(h*!%(*&@)"
Session(app)

secret_number = None
secret_length = None
# Function to create the quantum oracle
def apply_oracle(secret):
    num_of_bit = len(secret)
    oracle_circuit = QuantumCircuit(num_of_bit + 1, num_of_bit)
    oracle_circuit.h(range(num_of_bit))
    oracle_circuit.x(num_of_bit)
    oracle_circuit.h(num_of_bit)
    oracle_circuit.barrier()

    for index, number in enumerate(reversed(secret)):
        if number == '1':
            oracle_circuit.cx(index, num_of_bit)

    oracle_circuit.barrier()
    oracle_circuit.h(range(num_of_bit))
    oracle_circuit.barrier()

    return oracle_circuit

# Function to create the Bernstein-Vazirani quantum circuit using the oracle
def q_circuit_create(secret):
    length = len(secret)
    circuit = QuantumCircuit(length + 1, length)

    # Apply the quantum oracle
    oracle = apply_oracle(secret)
    circuit.compose(oracle, range(length + 1), inplace=True)

    # Measure the qubits
    circuit.measure(range(length), range(length))

    return circuit

# Function to perform the quantum computation
def quantums(n, circuit):
    simulator =  Aer.get_backend('qasm_simulator')
    result = execute(circuit, backend=simulator, shots=1).result()
    counts =  result.get_counts()
    secret_number = list(counts.keys())[0]
    count = counts[secret_number]
    return secret_number, count


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
    return render_template('quantum_query.html')

@app.route('/process_enhance_type', methods=["POST", "GET"])
def process_user_enhance_choice():
    enhance_type = request.form['enhance_type']
    return redirect(url_for(enhance_type))

@app.route('/process_mobile_input',  methods=["POST"])
def process_mobile_input():
    global secret_number
    global secret_length
    secret_number = request.form.get("secretNumber")
    secret_length = request.form.get("secretLength")
    print("Received secret number:", secret_number)
    if not secret_number:
        print("Error: Secret number not received from the form.")
    else:
        session['secretNumber'] = secret_number
        session['secretLength'] = secret_length
        print("Session Secret Number",session['secretNumber'])
    return render_template('mobile_end.html', secretNumber=secret_number)

@app.route('/process_game_type', methods=["POST", "GET"])
def process_game_type():
    global secret_number
    global secret_length
    if secret_number is None:
        secret_number = request.form["secretNumbers"]
        secret_length = request.form["secretLength"]
    game_type = request.form['gameType']
    

    session['n_length'] = int(secret_length)
    session['s_number'] = secret_number

    return redirect(url_for(game_type))

@app.route('/player_game')
def player_game():
    global secret_number
    global secret_length

    n_length = session.get('n_length')
    s_number = session.get('s_number')
    secret_number = None 
    secret_length = None
    return render_template("player_game.html", n_length=n_length, s_number=s_number)

@app.route("/classic_computer_game")
def classic_computer_game():
    global secret_number
    global secret_length
    n_length = session.get('n_length')
    s_number = session.get('s_number')
    secret_number = None 
    secret_length = None
    return render_template("classic_computer_game.html", n_length=n_length, s_number=s_number)

@app.route("/quantum_computer_game")
def quantum_computer_game():
    global secret_number
    global secret_length
    n_length = session.get('n_length')
    s_number = session.get('s_number')
    if s_number is None or s_number is "":
        s_number = ''.join(random.choice('01') for _ in range(n_length))
    s_number, tries = quantums(len(s_number), q_circuit_create(s_number))
    secret_number = None 
    secret_length = None
    return render_template("quantum_computer_game.html", s_number=s_number, secret_numbers=s_number, tries=tries, n_length=n_length)

@app.route('/play_again')
def play_again():
    return render_template("quantum_query.html")

@app.route("/not_play_again")
def not_play_again():
    return render_template("index.html")

@app.route('/enchancement')
def enchancement():
    return render_template("image_video.html")

@app.route('/quantum')
def quantum():
    qr_path = generate_qr_code("user_mob_form")
    return render_template("quantum_query.html", qr_path = qr_path)

# Route for mobile.html
@app.route('/user_mob_form', methods=["GET"])
def mobile_input():
    return render_template('user_mob.html')

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
        media = request.files['media']
        filename = media.filename
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

        file = request.files['image']
        filename = file.filename
        file_path = os.path.join(target_dir, filename)
        file.save(file_path)

        CODEFORMER_FIDELITY = 0.9
        BACKGROUND_ENHANCE = True
        FACE_UPSAMPLE = True

        if BACKGROUND_ENHANCE:
            if FACE_UPSAMPLE:
                command = f"python inference_codeformer.py -w {CODEFORMER_FIDELITY} --input_path ./static/images/user_upload --bg_upsampler realesrgan --face_upsample"
            else:
                command = f"python inference_codeformer.py -w {CODEFORMER_FIDELITY} --input_path ./static/images/user_upload --bg_upsampler realesrgan"
        else:
            command = f"python inference_codeformer.py -w {CODEFORMER_FIDELITY} --input_path ./static/images/user_upload"

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
