# 草榴社区自动邀请注册脚本

## 功能和作用

该脚本旨在自动化扫描草榴社区 **<技术讨论区>** 的最新帖子，并寻找包含特定关键字的帖子，如"**发码**"。  
一旦找到相关帖子，脚本将扫描其内容，以获取用户分享的邀请码。**同时支持文本码与图片码识别。**

这个脚本非常适用于那些希望自动获取邀请码的用户，避免手动浏览和筛选大量帖子的麻烦。

它能够自动处理邀请码的掩码，生成可能存在的所有字符，并且持续尝试匹配，直到找到可用的邀请码，然后使用该邀请码进行用户注册。

## 安装和配置

### 安装

1. 安装 Python 3.9 运行环境

2. 安装 依赖库

```
pip3 install ddddocr
pip3 install --force-reinstall -v "Pillow==9.5.0"
pip3 install beautifulsoup4
pip3 install requests
```

### 配置 (config.yaml)

> 将配置文件 config.example.yml，重命名为 config.yml

1. 配置要注册的用户名/密码/邮箱 (可以配置多个,强烈建议只配一个)
    ```yml
    registered_users:
      - mail: yourfirstmail@hotmail.com
        user_name: yourfirstusername
        password: yourfirstpassword
    ```

2. 配置掩码匹配规则
   > 如果某字符 '#' 要包含字母与数字, 则规则为:  
   > '#': "0123456789abcdefghijklmnopqrstuvwxyz"

    ```yml
    mask_rule:
      '*': "0123456789"
      '#': "0123456789"
      '¥': "0123456789"
      '@': "0123456789"
      '?': "0123456789"
    ```
3. 配置帖子标题关键字
   > 只扫描第一页标题包含 "码" 的帖子
    ```yml
    filter_keywords:
      - "码"
    ```
4. 其他配置 (可选)
    - proxy: 配置 http 代理
      ```yaml
      proxy:
        http: http://127.0.0.1:7890
        https: http://127.0.0.1:7890
      ```
    - mask_count_max: 最大支持的掩码位数 (建议配置为 2,配置过多会降低匹配效率)
    - interval_time_min/interval_time_max: 最大最小间隔时间 (脚本会取平均值,间隔时间过小容易被封 IP)
    - reverse: 反转倒叙 (将获取到的邀请码倒叙匹配)
    - input_mask: 手动录入邀请码
      ```yaml
      input_mask:
        - "123456*1234*1234"
        - "123*1234*1234567"
      ```
    - img_ocr: 图片识别 (当解析某个帖子, 获取不到文本邀请码时,脚本会尝试 ocr 识别帖子图片,来获取邀请码)
      ```yaml
      img_ocr:
        app_key: "xxxxxx"
        secret: "xxxxxxxxx"
      ``` 
      > 脚本支持 有道云 OCR 识别,请自行申请注册 (https://ai.youdao.com/DOCSIRMA/html/ocr/api/tyocr/index.html)
    - dingding_notify_access_token: (注册成功会发送消息提醒推送)
      ```yaml
      dingding_notify_access_token: "xxxx"
      ```
5. 消息提醒推送  
   notify_msg() 函数为注册成功后推送提醒,请自行实现

## 运行

```
python3 t66y_auto_register.py
```

![](img/success.png)

## 注意事项

- 该脚本涉及获取用户分享的邀请码等敏感信息，请仅用于学习与研究目的。
- 请确保遵循草榴社区的准则和法律合规性。

## 贡献

如果你对项目有兴趣或想要为项目做贡献，你可以提交 issue 或者 Pull Request。

## 捐赠

**如果感觉对您有帮助，请作者喝杯咖啡吧，请注明您的名字或者昵称，方便作者感谢o(*￣︶￣*)o**

|         **ALIPAY**          |         **WECHAT**          |
|:---------------------------:|:---------------------------:|
| ![](doc/wechat_resized.jpg) | ![](doc/alipay_resized.jpg) |
