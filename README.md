# CET
四六级准考证找回

# 说明
1. 系统来自另外一个大佬开源(https://github.com/LDouble/CET/)


# 使用方法
1. 按照依赖
```
pip install -r requirements.txt
```
2. 运行
```
python app.py # 测试环境
gunicorn -c gunc.py app:app # 用gunicorn部署
```
# 原理
1. 利用requests访问http://cet-bm.neea.edu.cn/
2. 获取验证码，利用flask提供api支持，并返回cookie
3. 提交后，下载准考证，然后解压并读取pdf用正则进行匹配即可。
4. 返回给用户
