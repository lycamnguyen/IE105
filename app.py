from flask import Flask, render_template, request, redirect, send_from_directory, url_for
import os
from werkzeug.utils import secure_filename
import numpy
import os
import imageio
import array


app = Flask(__name__)
app.config['OUTPUT_FOLDER'] = 'output_dir/' 
app.config['UPLOAD_DIRECTORY'] = 'input_dir/'
app.config['ALLOWED_EXTENSIONS'] = ['.png']


number_of_samples = 10000

def is_exe(input_file):
    ext = os.path.splitext(os.path.basename(input_file))[1].lower()
    print('ext = ', ext)
    result = False
    if '.exe' == ext:
        result = True
    return result

def generate_and_save_image(input_dir, output_dir, filename):
    out_file = os.path.splitext(os.path.basename(filename))[0] + '.png'
    out_file_full = output_dir + out_file
    input_file_path = os.path.join(input_dir, filename)
    print("out_file_full: ", out_file_full)
    if is_exe(filename):
        f = open(input_file_path, 'rb')
        ln = os.path.getsize(input_file_path)  # length of file in bytes
        width = 256
        rem = ln % width

        a = array.array("B")  # uint8 array
        a.fromfile(f, ln - rem)
        f.close()
        g = numpy.reshape(a, (len(a) // width, width))
        g = numpy.uint8(g)
        #print("g: ", g)
        imageio.imwrite(out_file_full, g)  # save the image
    else:
        print("not exe")

def convert_bin_to_img(input_dir, output_dir):
    if not os.path.isdir(input_dir):
        print(input_dir, 'Input directory not found. Exiting.')
        exit(0)
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    count = 0
    files = os.listdir(input_dir)
    print(files)
    for filename in files:
        print("filename: ", filename)
        try:
            generate_and_save_image(input_dir, output_dir, filename)
            print(filename)
            count += 1
            print(count)
            if number_of_samples == count:
                exit(0)
        except:
             print('Ignoring ', filename)


# Route để hiển thị giao diện người dùng và xử lý file PE
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            return redirect(request.url)

        if file and is_exe(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_DIRECTORY'], filename))
            generate_and_save_image(app.config['UPLOAD_DIRECTORY'], app.config['OUTPUT_FOLDER'], filename)
    files = os.listdir(app.config['OUTPUT_FOLDER'])
    images = []

    for file in files:
        extension = os.path.splitext(file)[1].lower()
        if extension in app.config['ALLOWED_EXTENSIONS']:
            images.append(file)

    return render_template('index.html', images=images)

@app.route('/image/<filename>', methods=['GET'])
def display_image(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)