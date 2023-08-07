import os, shutil, subprocess
import sys
temp_folder = './static/videos/tmp_frames'
result_folder = './static/videos/results'

if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

if len(sys.argv) > 1:
        file_name = sys.argv[1]
        print("File name: ",file_name)
input_path = f'./static/videos/user_upload/{file_name}'

print(input_path)
if os.path.isdir(temp_folder):
  shutil.rmtree(temp_folder)

os.mkdir(temp_folder)
print(f'Extracting Frames to: {temp_folder}')
cmd = [
       'ffmpeg',
       '-i',
       input_path,
       '-qscale:v',
       '1',
       '-qmin',
       '1',
       '-qmax',
       '1',
       '-vsync',
       '0',
       f'{temp_folder}/frame_%08d.png'
]

process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()
if process.returncode != 0:
    print(stderr)
    raise RuntimeError(stderr)
else:
    frame_count = len(os.listdir(f'{temp_folder}'))
    print(f"Done, Extracted {frame_count} Frames")


#@markdown # **4) Run ERSGAN on Extracted Frames!**
frame_count = len(os.listdir(f'{temp_folder}'))
print(f"Enhancing {frame_count} Frames with ESRGAN...")
cmd = [
       'python',
       'Real-ESRGAN/inference_realesrgan.py',
       '-n',
       'RealESRGAN_x4plus',
       '-i',
       f'{temp_folder}',
       '--outscale',
       '4',
       '--face_enhance'
]

process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()

if process.returncode != 0:
    print(stderr)
    raise RuntimeError(stderr)
else:
    print("Done Enhancing Frames")

#@markdown # **5) Recreate Video From Enhanced Frames!**

frame_count = len(os.listdir(f'{temp_folder}'))
if os.path.isdir(result_folder):
  shutil.rmtree(result_folder)
os.mkdir(result_folder)

fps = 25 #@param {type: "number"}
print(f"Recompiling {frame_count} Frames into Video...")
cmd = [
       'ffmpeg',
       '-i',
       f'./results/frame_%08d_out.png',
       '-c:a',
       'copy',
       '-c:v',
       'libx264',
       '-r',
       str(fps),
       '-pix_fmt',
       'yuv420p',
       f'{result_folder}/enhanced_{file_name}'
]
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()
if process.returncode != 0:
    print(stderr)
    raise RuntimeError(stderr)
else:
    print("Done Recreating Video")