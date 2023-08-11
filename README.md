# 草榴社区自动邀请注册脚本

## 功能和作用

**这是一个用于自动获取草榴社区邀请码并注册的 Python 脚本。**

该脚本旨在自动化扫描草榴社区 **<技术讨论区>** 的最新帖子(一小时内发布)，并寻找包含特定关键字的帖子，如"**发码**"。  
一旦找到相关帖子，脚本将扫描其内容，以获取用户分享的邀请码。**同时支持文本码与图片码识别。**  

它具备自动处理邀请码**掩码**的能力，能够生成所有可能存在的字符组合，并持续尝试匹配，直到找到有效的邀请码。一旦成功获取可用的邀请码，系统将使用该邀请码进行用户注册。


### 功能特点

- 多用户注册
- 验证码识别/文本邀请码以及图片邀请码识别
- 支持自定义掩码规则和过滤标题关键词。
- 可配置代理和请求间隔时间。
- 集成钉钉消息通知功能。

## 安装和配置

### 安装

1. 安装 Python 3.9 运行环境

2. 安装 依赖库

```
pip3 install ddddocr
pip3 install --force-reinstall -v "Pillow==9.5.0"
pip3 install pyyaml
pip3 install beautifulsoup4
pip3 install requests
```
3. 环境变量
```
# 日志级别 DEBUG/INFO/WARNING/ERROR, 默认:INFO
LOG_LEVEL=INFO
```

### 配置 (config.yaml)

**将配置文件 config.example.yml，重命名为 config.yml**

1. 配置要注册的用户名/密码/邮箱 (可以配置多个,**强烈建议只配一个**)
    ```yml
    registered_users:
      - mail: yourfirstmail@hotmail.com
        user_name: yourfirstuser
        password: yourfirstpassword
    ```

2. 配置掩码匹配规则
   > 字母只会是abcdef中的，其他20个字母不会出现在邀请码里面的
   > 如果某字符 '#' 要包含字母与数字, 则规则为:  
   > '#': "0123456789abcdef"  

    ```yml
    mask_rule:
      '*': "0123456789"
      '#': "0123456789"
      '¥': "0123456789"
      '@': "0123456789"
      '?': "0123456789"
    ```
3. 配置帖子标题关键字
   **持续实时扫描第一页标题包含 "码" 的(一小时内发布)最新帖子**
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
    - interval_time_min/interval_time_max: 最大最小间隔时间 (脚本会取范围内的随机值,**间隔时间过小容易被封 IP**)
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
      > 当前实现为 <钉钉机器人消息推送> ,若想自定义请重写 notify_msg() 函数
      > https://open.dingtalk.com/document/orgapp/custom-robots-send-group-messages
      ```yaml
      dingding_notify_access_token: "xxxx"
      ```

## 运行

```
python3 t66y_auto_register.py
```

![](img/success.png)

## 免责声明

- 本脚本仅供学习和研究使用，请勿将其用于非法活动。
- 对于使用本脚本造成的任何违法行为或损失，作者不承担任何责任。


## 贡献

如果你对项目有兴趣或想要为项目做贡献，你可以提交 issue 或者 Pull Request。

## 捐赠

**如果感觉对您有帮助，请作者喝杯咖啡吧，请注明您的名字或者昵称，方便作者感谢o(*￣︶￣*)o**

|         **WECHAT**          |         **ALIPAY**          |
|:---------------------------:|:---------------------------:|
| ![](doc/wechat_resized.jpg) | ![](doc/alipay_resized.jpg) |
