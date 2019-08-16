from gevent import monkey
monkey.patch_all()
from flask import Flask, jsonify, render_template, request
import requests
import base64
import re
import zipfile
from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from io import StringIO
from io import open
import json
import os

def getHttpStatusCode():
    userAgent = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0"} # 添加一个user-agent,访问反爬虫策略严格的网站很有用
    timeOut = 4 # 请求超时时间设置为4秒
    try:
        request = requests.get("http://imnu.52king.cn/1.php", headers = userAgent, timeout = timeOut)
        httpStatusCode = request.status_code
        return httpStatusCode
 
    except requests.exceptions.HTTPError as e:
        return e

def readPDF(pdfFile):
    pdfFile = open(pdfFile, "rb")
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)

    process_pdf(rsrcmgr, device, pdfFile)
    device.close()

    content = retstr.getvalue()
    retstr.close()
    pdfFile.close()
    return content


def getcode(text):
    code = re.findall(r"准考证号：(\d+)", text)
    name = re.findall(r"姓名：(.+)\n", text)
    if code:
        code = code[0]
    else:
        code = None
    if name:
        name = name[0]
    else:
        name = None
    if code is not None:
        return {"code": code, "name": name}
    else:
        return None


def un_zip(file_name):
    """unzip zip file"""
    zip_file = zipfile.ZipFile(file_name)
    for names in zip_file.namelist():
        file = (zip_file.extract(names, "./data/"))
    zip_file.close()
    os.remove(file_name) # 删除文件，本地不进行保存
    return file

coed = getHttpStatusCode()
if coed == 200 :
    print("欢迎使用国王网络Pro四六级找回系统")
else:
    exit(0);

def down(sid):
    r = requests.get("http://cet-bm.neea.edu.cn/Home/DownTestTicket?SID=" + sid)
    data = r.content
    with open("data/" + sid + ".zip", "wb") as f:
        f.write(data)
    return "data/" + sid + ".zip"


def _query(province, code, name, number, cookie):
    jar = requests.cookies.RequestsCookieJar()
    cookie = cookie.split("分")
    jar.set('ASP.NET_SessionId', cookie[0], domain='cet-bm.neea.edu.cn', path='/')
    jar.set('BIGipServercet_pool', cookie[1], domain='cet-bm.neea.edu.cn', path='/')
    param = dict(provinceCode=province, IDTypeCode=1, IDNumber=number, Name=name, verificationCode=code)
    r = requests.post("http://cet-bm.neea.edu.cn/Home/ToQuickPrintTestTicket", param, cookies=jar)
    text = r.text
    data = None
    try:
        jsonld = json.loads(text)
        if jsonld.get("ExceuteResultType") == 1:
            ddd = jsonld.get("Message")
            sid = ddd[9:137]
            print(sid)
            if sid:
                file = down(sid)
                file = un_zip(file)
                text = readPDF(file)
                code = getcode(text)
                if code.get("code"):
                    data = code
                    ExceuteResultType = 1
                    Message = "查询成功"
                else:
                    Message = "查询失败"
                    ExceuteResultType = -1
        else:
            return jsonld
    except Exception as e:
        print(e)
        ExceuteResultType = -1
        Message = "系统错误"
    return dict(ExceuteResultType=ExceuteResultType, Message=Message, data=data)


app = Flask(__name__)


@app.route("/code")
def code():
    """
    获取验证码,返回cookie，和 验证码的b64
    :return:
    """
    r = requests.get("http://cet-bm.neea.edu.cn/Home/VerifyCodeImg")
    print((r.cookies))
    cookies = r.cookies['ASP.NET_SessionId'] + "分" + r.cookies['BIGipServercet_pool']
    content = r.content
    img = 'data:image/jpeg;base64,' + base64.b64encode(content).decode()
    return jsonify({"data": img, "cookie": cookies})


@app.route('/')
def hello_world():
    """
    获取页面
    :return:
    """
    return render_template("index.html")


@app.route('/query', methods=['POST', 'GET'])
def query():
    """
    province: province,
    number: number,
    code: code,
    name: name,
    :return:
    """
    province = request.form.get("province")
    number = request.form.get("number")
    code = request.form.get("code")
    name = request.form.get("name")
    cookie = request.form.get("cookie")
    if province and number and code and name and cookie:
        return jsonify(_query(province, code, name, number, cookie))
    else:
        return jsonify({"ExceuteResultType": '-1', "Message": "信息不全"})


if __name__ == '__main__':
    app.run(
        host = '0.0.0.0',
        port = 5000,
        debug=True)
