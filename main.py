from flask_cors import CORS
from flask import Flask, send_from_directory, send_file, request
import json
import csv
import os
import hashlib
import warnings
import pandas as pd
warnings.filterwarnings("ignore")
charset = "utf8"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = r"file"
CORS(app)


@app.route('/test', methods=['GET','POST'])
def test():
    return 'success'

@app.route('/uploadDemand/<time>', methods=['POST'])
def upload_demand(time):
    file_obj = request.files.getlist("file")
    file_info = dict(request.form)
    response = {'code': 0, 'msg': 'success'}
    exist_demand_title = []
    with open('demand_title.csv', 'r', newline='') as new_file:
        csv_file = csv.reader(new_file)
        for line in csv_file:
            if len(line) != 0:
                exist_demand_title.append(line[0])
    if file_info['title'] in exist_demand_title:
        response['code'] = -1
        response['msg'] = '标题已存在，请修改后重新提交'
        return response

    # 写入标题，写入表单
    with open('demand_title.csv', 'a+', newline='') as new_file:
        csv_writer = csv.writer(new_file)
        csv_writer.writerow([file_info['title']])

    title = file_info['title']
    detail = file_info['detail']
    name = file_info['name']
    email = file_info['email']
    address = file_info['address']
    with open('demand.csv', 'a+', newline='') as new_file:
        csv_writer = csv.writer(new_file)
        csv_writer.writerow([title, detail, name, email, address])
    return response

@app.route('/uploadFile/<time>', methods=['POST'])
def upload_file(time):
    file_obj = request.files.getlist("file")
    print(file_obj)
    file_info = dict(request.form)
    response = {'code': 0, 'msg': 'success'}

    exist_file_title = []
    with open('file_title.csv', 'r', newline='') as new_file:
        csv_file = csv.reader(new_file)
        for line in csv_file:
            if len(line) != 0:
                exist_file_title.append(line[0])
    print(exist_file_title)
    if file_info['title'] in exist_file_title:
        response['code'] = -1
        response['msg'] = '标题已存在，请修改后重新提交'
        return response

    # 存储文件，写入标题，写入表单
    with open('file_title.csv', 'a+', newline='') as new_file:
        csv_writer = csv.writer(new_file)
        csv_writer.writerow([file_info['title']])
    # 存储文件

    # 写入表单
    # time存在，参数
    title=file_info['title']
    detail=file_info['detail']
    tags=file_info['tags']
    is_file=int(file_info['is_file']) #0代表没有文件， 1代表有文件
    file_path = ''
    dir_path = os.path.join(app.config['UPLOAD_FOLDER'], time)
    os.mkdir(dir_path)
    if is_file == 1:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], time, file_obj[0].filename)
        file_obj[0].save(file_path)
    file_link = file_info['file_link']
    is_img = int(file_info['is_img']) #0代表没有图片，1~n代表有图片
    img_path = ''
    print(is_img)
    if is_img != 0:
        img_path = []
        for index in range(is_img):
            img_path.append(os.path.join(app.config['UPLOAD_FOLDER'], time, file_obj[index+is_file].filename))
            file_obj[index+is_file].save(img_path[index])
    name = file_info['name']
    email = file_info['email']
    address = file_info['address']
    with open('form.csv', 'a+', newline='') as new_file:
        csv_writer = csv.writer(new_file)
        csv_writer.writerow([
            title,
            detail,
            tags,
            is_file,
            file_path,
            file_link,
            is_img,
            img_path,
            time,
            name,
            email,
            address
        ])
    return response


@app.route('/deleteFile', methods=['POST'])
def delete_file():
    title = dict(request.form)['title']
    titles = pd.read_csv('./file_title.csv')
    form = pd.read_csv('./form.csv')
    line_num = -1
    with open('file_title.csv', 'r', newline='') as new_file:
        csv_file = csv.reader(new_file)
        for index, line in enumerate(csv_file):
            if line[0] == title:
                line_num = index
    if line_num == -1:
        return {
            'code': -1,
            'msg': '找不到文件'
        }
    # 删除文件和目录
    is_file = form.iat[line_num, 4]
    is_img = form.iat[line_num, 7]

    if is_img:
        img_path = form.iat[line_num, 8]
        os.remove(img_path)
    if is_file:
        file_path = form.iat[line_num, 8]
        os.remove(file_path)
    if is_file or is_img:
        time = form.iat[line_num, 9]
        dir_path = os.path.join(app.config['UPLOAD_FOLDER'], time)
        os.rmdir(dir_path)

    # 删除表单项，标题项
    titles.drop([line_num], inplace=True)
    form.drop([line_num], inplace=True)

    titles.to_csv("file_title.csv", index=False, encoding="utf-8")
    form.to_csv("form.csv", index=False, encoding="utf-8")

    return {
        'code': 0,
        'msg': 'success'
    }


@app.route('/getList', methods=["GET"])
def get_list():
    response = {
        'code': 0,
        'msg': 'success',
        'list': []
    }
    with open('form.csv', 'r', newline='') as new_file:
        csv_file = csv.reader(new_file)
        for index, line in enumerate(csv_file):
            if index == 0:
                continue
            if len(line) != 0:
                response['list'].append(line)
    return response

@app.route('/getDemandList', methods=["GET"])
def get_demand_list():
    response = {
        'code': 0,
        'msg': 'success',
        'list': []
    }
    with open('demand.csv', 'r', newline='') as new_file:
        csv_file = csv.reader(new_file)
        for index, line in enumerate(csv_file):
            if index == 0:
                continue
            if len(line) != 0:
                response['list'].append(line)
    return response

@app.route('/downloadFile/<title>', methods=["GET"])
def download_file(title):
    line_num = -1
    form = pd.read_csv('./form.csv')
    with open('file_title.csv', 'r', newline='') as new_file:
        csv_file = csv.reader(new_file)
        for index, line in enumerate(csv_file):
            if line[0] == title:
                line_num = index
    if line_num == -1:
        return {
            'code': -1,
            'msg': '找不到文件'
    }
    file_path = form.iat[line_num, 4]
    return send_file(file_path, as_attachment=True)


@app.route('/getImg/<title>/<num>')
def get_img(title, num):
    line_num = -1
    form = pd.read_csv('./form.csv')
    with open('file_title.csv', 'r', newline='') as new_file:
        csv_file = csv.reader(new_file)
        for index, line in enumerate(csv_file):
            if line[0] == title:
                line_num = index
    if line_num == -1:
        return {
            'code': -1,
            'msg': '找不到文件'
        }

    file_path = form.iat[line_num, 7][2: -2].split("', '")
    print(file_path[0])
    return send_file(file_path[int(num)])


@app.route('/feedback', methods=["POST"])
def feedback():
    f = dict(request.form)['feedback']
    with open('feedback.csv', 'a+', newline='') as new_file:
        csv_writer = csv.writer(new_file)
        csv_writer.writerow([f])

    return {
        'msg': "success",
        'code': 0
    }


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False, port=8889)
