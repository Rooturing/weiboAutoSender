## Python自动登陆发微博小程序

### 介绍

由于微博自身提供的SDK限制较多，而且申请审核时间长，因此决定自己写一个小程序，完成免人工操作，批量从RSS源获取数据并发微博的功能。

使用前的配置：

+ 在config.py中设置好微博的登陆账号密码，以及RSS源的URL地址
+ 填写连接MySQL数据库的用户密码，以及提前创建好的相应数据库名
+ 配置是否使用proxy，以便于调试
+ 配置是否记录运行日志
+ 设置每次发送微博的间隔时长
+ 安装requirements.txt中的依赖库 `pip install -r requirements.txt`

使用方法：

+ 在linux服务器上配置`crontab -e`
+ 添加定时任务 `0 12 * * * python ~/weiboAutoSender/main.py` 每天12:00准时爬取RSS上的消息并发微博

更多详细过程分析，请查看文章[新浪微博登陆过程详解以及Python小程序实现](https://blog.ssssamaritan.xyz/2019/03/16/%E6%96%B0%E6%B5%AA%E5%BE%AE%E5%8D%9A%E7%99%BB%E9%99%86%E8%BF%87%E7%A8%8B%E8%AF%A6%E8%A7%A3%E4%BB%A5%E5%8F%8APython%E5%B0%8F%E7%A8%8B%E5%BA%8F%E5%AE%9E%E7%8E%B0/)
