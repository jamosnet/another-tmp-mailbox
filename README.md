

感谢 [rev1si0n/another-tmp-mailbox](https://github.com/rev1si0n/another-tmp-mailbox) 用简短的代码实现了匿名邮箱最主要的功能，我在此基础上做了一些改动
1. 支持多域名，python  main.py  --domain=aa.com,bb.com --clean_seconds=3600
    > 特别说明一下， 1234@aa.com和1234@bb.com本程序是不做区分的，只认邮箱@前面的名称
    
2. 支持接收任何收件人的邮件（邮箱不需要先创建）。有这样的场景，我们在注册一个网站时候需要用到邮箱，这时候可以直接胡编乱造一个，然后再来网站收取邮件。
3. 支持自定义邮箱，规则是 ([a-z0-9]{4,12})
4. 可以自定义邮件保留时间。
5. docker run 部署
    ```
    # cd 到源码文件夹
    $ docker build -t tmpmail .
    # 等待结束，随后自行修改下方 yaml 中的 domain 及相关端口配置
    docker run -it --rm -v /data/tmpmail:/tmpmail -p 25:25 -p 8080:8080 tmpmail python3 -u /usr/local/tmpmail/main.py -port=8080 -domain=example.com
    ```
6. 用python做了一个调用的Wrapper，方便集成到其他项目代码中

[虚拟环境配置看这里venv.md](venv.md)

本地测试需要设置hosts , 位置在 C:\Windows\System32\drivers\etc\
```
127.0.0.1   aa.com
127.0.0.1   bb.com
```
----
无需注册，独立邮箱地址，支持富文本的邮件（html），支持 RSS 订阅，自动刷新，可手动删除账号。

 
### 这是干嘛的

**这种类型的邮箱服务通常被用于避免垃圾邮件、保护个人隐私或测试应用程序等场合。**。比如你需要临时在一个网站注册账号，他需要你邮箱账号，这种情况下，我是不愿意使用我的真实邮箱去注册的，因为我不相信这个网站，其次我会尽量减少信息泄露的途径。又比如你在看xhz，要你注册账号才能下载，好了，用自己邮箱又是不太合适的地方。这时我一般会去找一些公开注册的网站新建一个邮箱。其实现成的服务挺多的，比如比较著名的 `yopmail` 就是一个类似的邮箱，你甚至不需要注册。

但是现在国内可以用邮箱注册账号的地方基本没有了，注册账号百分之99都需要手机号。而且国内对于邮箱的使用并不太流行，但是个人觉得这对我还是有用处的。

> 这个服务只能接收邮件并不能发送邮件。

因为垃圾邮件的的原因，目前所知的全球任何一家正规服务器提供商，默认都不会给你开放邮件端口的出网邮件。

### 如何自己部署

进行之前，请先确保云服务厂商允许25端口入站以及安全组/防火墙设置运行了25端口。
目前已知情况，阿里云的服务器默认25端口可以入站，所以你只需要将安全组设置运行25端口TCP即可。

随后，编辑要绑定域名的DNS解析记录，假设域名为 example.com
新建解析 (A)，主机记录 @，记录值填写为云服务器的IP。新建解析 (MX)，主机记录 @，记录值 example.com，MX优先级默认


例如如下配置，123.123.123.123 代表你的服务器IP，mail.example.com 是访问此邮箱页面的主机名，example.com 是邮箱的后缀例如 abcdef@example.com。


|主机记录|记录类型|记录值|TTL|
|  ----  | ----  | ----  | ----  |
|mail|CNAME|example.com|10分钟|
|@|MX|example.com|10分钟|
|@|A|123.123.123.123|10分钟|

这样，你已经完成了域名相关的配置，随后进入云服务器进行以下操作。

```bash
# cd 到源码文件夹
$ docker build -t tmpmail .
# 等待结束，随后自行修改下方 yaml 中的 domain 及相关端口配置
# 找到 ["python3", "-u", "/usr/local/tmpmail/main.py", "-port=8080", "-domain=YOUR.DOMAIN"]
# 将 8080 修改为你想要的端口（用来web访问），将 YOUR.DOMAIN 修改为你的域名，随后启动即可
$ docker-compose -f docker-compose.yaml up -d
```

### 演示截图:
![或者查看项目里的 screenshot.png](screenshot.png)

### 查看邮件的截图:
![或者查看项目里的 screenshot2.png](screenshot2.png)

Enjoy~
