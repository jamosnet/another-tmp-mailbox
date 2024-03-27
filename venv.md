新建虚拟环境，我用的本地环境是win10 + PyCharm 2018.3.7(Community Edition)

### 查看当前环境
pip list
```buildoutcfg
Package    Version
---------- -------
pip        10.0.1
setuptools 39.1.0

```
### 更新pip和安装依赖包

``` 
python -m pip install --upgrade pip   -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m pip install -U --force-reinstall pip   -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install --upgrade setuptools wheel   -i https://pypi.tuna.tsinghua.edu.cn/simple

pip install -i https://pypi.tuna.tsinghua.edu.cn/simple  mail-parser==3.15.0
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple  tornado==6.4
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple  peewee==3.17.1
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple  aiosmtpd==1.4.5

```
安装好依赖后是这样的
```buildoutcfg
Package     Version
----------- -------
aiosmtpd    1.4.5
atpublic    4.0
attrs       23.2.0
mail-parser 3.15.0
peewee      3.17.1
pip         24.0
setuptools  39.1.0
simplejson  3.19.2
six         1.16.0
tornado     6.4
wheel       0.43.0

```

### 如果要同时调试 tempmailbox.py 还要安装依赖包
    ```
    pip3 install  -i https://pypi.tuna.tsinghua.edu.cn/simple   requests[socks]
    ```