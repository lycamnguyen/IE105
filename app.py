from flask import Flask, render_template, request, redirect, send_from_directory, send_file
import zipfile
import os
from werkzeug.utils import secure_filename
import numpy
import array
import time
import cv2


app = Flask(__name__)
app.config['OUTPUT_FOLDER'] = 'output/'
app.config['UPLOAD_DIRECTORY'] = 'input/'
app.config['ALLOWED_EXTENSIONS'] = ['.png']


color = 0


def is_pe(fileName):
    # tách tập tin thành phần cơ sở và mở rộng
    parts = os.path.splitext(fileName)
    extension = parts[-1]  # Lấy phần mở rộng
    # kiểm tra phần mở rộng
    return extension.lower() in [".exe", ".dll", ".ocx", ".sys", ".ime", ".cpl", ".bpl", ".ime", ".tlb", ".ocx", ".res", ".ax"]


def generate_image(input, output, fileName, color):

    # lấy tên cơ sở của tệp tin PE (phần trước dấu chấm .) và thêm phần mở rộng .png để tạo tên tệp tin hình ảnh đầu ra.
    out_file = os.path.splitext(os.path.basename(fileName))[0] + '.png'
    # tạo đường dẫn của hình ảnh đầu ra.
    out_file_full = os.path.join(output, out_file)
    input_file_path = os.path.join(input, fileName)  # đường dẫn chứa tập PE

    if is_pe(fileName):
        # mở tệp tin để đọc trong chế độ nhị phân.
        open_pe = open(input_file_path, 'rb')
        # lấy kích thước của tệp tin (độ dài tệp tin theo byte).
        len_pe = os.path.getsize(input_file_path)
        width = 256  # chiều rộng ảnh
        rem = len_pe % width  # kích thước dư
        # tạo một mảng dữ liệu kiểu uint8 để lưu trữ thông tin hình ảnh
        a = array.array("B")
        # đọc nội dung tệp tin PE vào mảng dữ liệu hình ảnh, bỏ qua phần còn lại của tệp tin nếu kích thước không chia hết cho 256 byte.
        a.fromfile(open_pe, len_pe - rem)
        open_pe.close()
        # chuyển đổi mảng dữ liệu hình ảnh thành ma trận hình ảnh, có chiều rộng bằng 256 pixel.
        g = numpy.reshape(a, (len(a) // width, width))
        # chuyển đổi loại dữ liệu của ma trận hình ảnh thành uint8
        g = numpy.uint8(g)
        # chuyển đổi mảng dữ liệu thành mảng ba chiều
        g = numpy.stack([g, g, g], axis=2)

        if color == "yellow":
            g = cv2.cvtColor(g, cv2.COLOR_BGR2LAB)
        elif color == "red":
            g = cv2.cvtColor(g, cv2.COLOR_BGR2HSV)
        elif color == "green":
            g = cv2.cvtColor(g, cv2.COLOR_BGR2HLS)
        else:
            g = g

        cv2.imwrite(out_file_full, g)
    else:
        print("not pe")


def convert_binary_to_img(input, output):

    count = 0
    files = os.listdir(input)  # danh sách các tệp trong input
    print(files)
    for filename in files:
        try:
            generate_image(input, output, filename)

        except:
            print('error', filename)

# Route để hiển thị giao diện người dùng và xử lý file PE


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    count_file = 0
    start_time = time.time()
    path_deleted_file = os.listdir('output/')
    path_deleted_file2 = os.listdir('input/')
    if (path_deleted_file):

        for file_name in path_deleted_file:
            path_file = os.path.join('output/', file_name)
            os.remove(path_file)

        for file_name in path_deleted_file2:
            path_file2 = os.path.join('input/', file_name)
            os.remove(path_file2)

    if request.method == 'POST':
        selected_color = request.form['color']
        print(selected_color)
        for file in request.files.getlist('file'):
            count_file += 1
            if file.filename == '':
                return redirect(request.url)

            if file and is_pe(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(
                    app.config['UPLOAD_DIRECTORY'], filename))

                generate_image(
                    app.config['UPLOAD_DIRECTORY'], app.config['OUTPUT_FOLDER'], file.filename, selected_color)
    files = os.listdir(app.config['OUTPUT_FOLDER'])
    images = []

    for file in files:
        extension = os.path.splitext(file)[1].lower()
        if extension in app.config['ALLOWED_EXTENSIONS']:
            images.append(file)
    end_time = time.time()

    return render_template('index.html', images=images, time_run=end_time-start_time,  num_files=count_file)


@app.route('/download_all_images', methods=['GET'])
def download_all_images():
    images_folder = app.config['OUTPUT_FOLDER']
    zip_filename = 'all_images.zip'

    # Create a zip file containing all images
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for image in os.listdir(images_folder):
            image_path = os.path.join(images_folder, image)
            zipf.write(image_path, os.path.basename(image_path))

    # Send the zip file as a response
    return send_file(zip_filename, as_attachment=True)


@app.route('/image/<filename>', methods=['GET'])
def display_image(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
