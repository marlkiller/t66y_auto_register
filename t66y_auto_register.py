import base64
import hashlib
import json
import logging
import os
import random
import re
import sys
import time
import uuid
from datetime import datetime
from itertools import product

# pip3 install ddddocr
# error module 'PIL.Image' has no attribute 'ANTIALIAS'
# pip3 install --force-reinstall -v "Pillow==9.5.0"
import ddddocr
import requests
import yaml
# pip3 install beautifulsoup4
from bs4 import BeautifulSoup
import importlib.metadata

LOGGER_FMT = '%(asctime)s %(filename)s-%(funcName)s-[%(lineno)d] - %(threadName)s [%(levelname)s]  : %(message)s'
LOGGER_DATA_FORMAT = '[%Y-%m-%d %H:%M:%S]'
CL_HOST = "https://t66y.com"

CURRENT_DATE = datetime.now()
# 全局变量, 存储实时获取到的邀请码
GLOBAL_CODE_MASK = []
# 全局变量, 已爬取解析过的的帖子 ID
GLOBAL_REPLIED_POST = []


def init_logging_basic(name=None, level="INFO"):
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter(fmt=LOGGER_FMT, datefmt=LOGGER_DATA_FORMAT)
    ch.setFormatter(formatter)
    if name:
        _logger = logging.getLogger(name)
    else:
        _logger = logging.getLogger()
    _logger.setLevel(level)
    _logger.addHandler(ch)
    return _logger


# 日志级别
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG = init_logging_basic(__name__, level=LOG_LEVEL)
LOG.info(f"log level is {LOG_LEVEL}")
# 当前文件路径
CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))

# 加载配置文件
try:
    with open(f"{CURRENT_FOLDER}{os.path.sep}config.yml", "r", encoding='utf8') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
except Exception as e:
    LOG.error("Loading the 'config.yml' fails")
    LOG.error(e)
    sys.exit()

dddd_ocr = None


def compared_version(ver1, ver2):
    """
    传入不带英文的版本号,特殊情况："10.12.2.6.5">"10.12.2.6"
    :param ver1: 版本号1
    :param ver2: 版本号2
    :return: ver1< = >ver2返回-1/0/1
    """
    list1 = str(ver1).split(".")
    list2 = str(ver2).split(".")
    # 循环次数为短的列表的len
    for i in range(len(list1)) if len(list1) < len(list2) else range(len(list2)):
        if int(list1[i]) == int(list2[i]):
            pass
        elif int(list1[i]) < int(list2[i]):
            return -1
        else:
            return 1
    # 循环结束，哪个列表长哪个版本号高
    if len(list1) == len(list2):
        return 0
    elif len(list1) < len(list2):
        return -1
    else:
        return 1


try:
    ddddocr_version = importlib.metadata.version("ddddocr")
    compare = compared_version(ddddocr_version, "1.0.6")
    # if ddddocr_version and ddddocr_version > "1.0.6":
    if compare > 0:
        dddd_ocr = ddddocr.DdddOcr(show_ad=False, ocr=True)
    else:
        dddd_ocr = ddddocr.DdddOcr()
except Exception as e:
    LOG.error("init 'ddddocr' fails")
    LOG.error(e)
    sys.exit()

# 要注册的用户列表
REGISTERED_USERS = config.get("registered_users", [])
# 配置代理
PROXY = config.get("proxy", {})
# 掩码规则
MASK_RULE = config.get("mask_rule", {})
MASK_RULE_KEYS = list(MASK_RULE.keys())

# 1234*#¥@?2341234
# [0-9a-f*#¥@?]{16}
INVITATION_CODE_REGEX = r'[0-9a-f%s]{16}' % "".join(MASK_RULE_KEYS)
# 自定义指定输入邀请码
INPUT_MASK = config.get("input_mask", [])
# 过滤标题关键词
FILTER_KEYWORDS = config.get("filter_keywords", [])
# 请求间隔下限(秒)
INTERVAL_TIME_MIN = config.get("interval_time_min", 2)
# 请求间隔上限(秒)
INTERVAL_TIME_MAX = config.get("interval_time_max", 5)
REVERSE = config.get("reverse", False)
# 是否显示等待进度条
SHOW_PROGRESS_BAR = config.get("show_progress_bar", False)

# 掩码数量上限
MASK_COUNT_MAX = config.get("mask_count_max", 2)

# 有道 OCR 图片识别
IMG_OCR = config.get("img_ocr", None)
DINGDING_NOTIFY_ACCESS_TOKEN = config.get("dingding_notify_access_token", None)

if REVERSE:
    REGISTERED_USERS = REGISTERED_USERS[::-1]


# 发送消息通知
def notify_msg(msg):
    try:
        if not DINGDING_NOTIFY_ACCESS_TOKEN:
            return
        url = f"https://oapi.dingtalk.com/robot/send?access_token={DINGDING_NOTIFY_ACCESS_TOKEN}"
        payload = json.dumps({
            "msgtype": "text",
            "text": {
                "content": msg
            },
            "at": {
                "isAtAll": False
            }
        })
        response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload)
        LOG.info(f"Send msg {msg}  --> {response.text}")
    except:
        pass


# 生成请求头
def generate_headers():
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': generate_random_user_agent(),
        'X-Forwarded-For': generate_random_ip(),
        'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    }


def generate_random_user_agent():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.3',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.3',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.3',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.3'
    ]
    return random.choice(user_agents)


def generate_random_ip():
    # ':'.join([hex(randint(2**16,2**17))[-4:] for x in range(8)])
    return ".".join(str(random.randint(0, 255)) for _ in range(4))


# 获取邀请码中掩码位数量
def count_non_alphanumeric(code_mask):
    non_alphanumeric = re.sub(r'[a-f0-9]', '', code_mask)
    return len(non_alphanumeric)


def sleep_with_progress_bar(wait_time):
    if wait_time <= 0:
        return
    if not SHOW_PROGRESS_BAR:
        time.sleep(wait_time)
        return
    for i in range(1, wait_time + 1):
        rate = i / wait_time
        rate_num = int(rate * 100)
        percent = f'{rate * 100:.2f}'

        r = '\rWaiting Secs: {} | [{}{}] {}%'.format(
            f"{wait_time}/{i}",
            "#" * rate_num,
            " " * (100 - rate_num),
            percent
        )
        sys.stdout.write(r)
        sys.stdout.flush()
        time.sleep(1)


# 根据掩码获取生成的所有邀请码数量
def calculate_possibilities_length(masks):
    possibilities_length = 1
    for mask in masks:
        if mask in MASK_RULE_KEYS:
            possibilities_length *= len(MASK_RULE.get(mask))
        else:
            possibilities_length *= len(mask)
    return possibilities_length


# 根据掩码生成邀请码列表
def generate_real_codes_with_mask(code_mask):
    possible_chars = []
    for ch in code_mask:
        if ch in MASK_RULE_KEYS:
            possible_chars.append(MASK_RULE.get(ch))
        else:
            possible_chars.append(ch)
    for code in product(*possible_chars):
        yield ''.join(code)


def generate_real_codes_with_mask_deprecated(code_mask):
    invite_codes = []
    possible_chars = []
    for ch in code_mask:
        if ch in MASK_RULE_KEYS:
            # string.ascii_lowercase + string.digits
            possible_chars.append(MASK_RULE.get(ch))
        else:
            possible_chars.append(ch)
    for code in product(*possible_chars):
        invite_codes.append(''.join(code))
    return invite_codes


# 自定义异常,频繁访问,IP被禁止
class BannedIPException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("Your IP is banned, Please change the network environment !!!", "nginx 403")


def filter_codes_by_mask_num(codes):
    for code in codes.copy():
        mask_count = count_non_alphanumeric(code)
        if mask_count > MASK_COUNT_MAX:
            LOG.warning(
                f"The number of bits of the mask is greater than {MASK_COUNT_MAX}, [{code}] will be skipped.")
            codes.remove(code)


class RegisteredTask:
    def __init__(self, registered_users):
        self.session = None
        self.user_name = registered_users.get("user_name")
        self.password = registered_users.get("password")
        self.mail = registered_users.get("mail")

    def start(self):
        global GLOBAL_CODE_MASK
        LOG.info(f"Registered task for [{self.user_name}] started.")
        self.init_session()

        if not self.check_user_status():
            return

        while True:
            if not GLOBAL_CODE_MASK or len(GLOBAL_CODE_MASK) == 0:
                read_input_mask = INPUT_MASK and len(INPUT_MASK) > 0
                if read_input_mask:
                    for code in INPUT_MASK:
                        match = re.match(INVITATION_CODE_REGEX, code)
                        if not match:
                            LOG.warning(
                                f"The invitation code is in the wrong format, [{code}] will be skipped.")
                            INPUT_MASK.remove(code)
                    filter_codes_by_mask_num(INPUT_MASK)
                    GLOBAL_CODE_MASK = INPUT_MASK
                else:
                    GLOBAL_CODE_MASK = self.search_post()
                    if not GLOBAL_CODE_MASK:
                        interval_time = random.randint(INTERVAL_TIME_MIN, INTERVAL_TIME_MAX)
                        sleep_with_progress_bar(interval_time)
                        continue
            if REVERSE:
                GLOBAL_CODE_MASK = GLOBAL_CODE_MASK[::-1]
            LOG.info(f"GLOBAL_CODE_MASK is {GLOBAL_CODE_MASK}")

            for code_mask in GLOBAL_CODE_MASK.copy():
                total_num = calculate_possibilities_length(code_mask)
                num = 0
                for code_real in generate_real_codes_with_mask(code_mask):
                    num = num + 1
                    process = f"{num}/{total_num}"
                    LOG.info(f"register_with_code_real [{process}] {code_mask}:{code_real}")
                    # if self.check_with_code_real(code_real) and self.register_with_code_real(code_real):
                    if self.register_with_real_code(code_real):
                        notify_msg(
                            f"Succeeded in registering the [{self.user_name}:{self.password}:{self.mail}] using the invitation code [{code_mask}:{code_real}]")
                        LOG.info(
                            f"Succeeded in registering the [{self.user_name}:{self.password}:{self.mail}] using the invitation code [{code_mask}:{code_real}]")
                        GLOBAL_CODE_MASK.remove(code_mask)
                        return
                GLOBAL_CODE_MASK.remove(code_mask)

    def init_session(self):
        self.session = requests.Session()
        self.session.proxies = PROXY

    # 检查用户名状态
    def check_user_status(self):
        while True:
            try:
                validate = self.get_validate()
                data = {
                    'username': self.user_name,
                    'validate': validate,
                    'action': 'regnameck',
                }
                response = self.session.post(f'{CL_HOST}/register.php?', headers=generate_headers(), data=data)
                if response.text.find("parent.retmsg('4')") != -1:
                    LOG.info(f"恭喜您，該用戶名 [{self.user_name}] 還未被註冊，您可以使用這個用戶名註冊！")
                    return True
                elif response.text.find("parent.retmsg('3')") != -1:
                    LOG.warning(f"該用戶名 [{self.user_name}] 已經被註冊，請選用其他用戶名")
                    return False
                elif response.text.find("parent.retmsg('1')") != -1:
                    LOG.warning(f"此用戶名 [{self.user_name}] 包含不可接受字符或被管理員屏蔽,請選擇其它用戶名")
                    return False
                elif response.text.find("parent.retmsg('0')") != -1:
                    LOG.warning(f"用戶名長度錯誤！ [{self.user_name}]")
                    return False
                elif response.text.find("parent.retmsg('5')") != -1:
                    LOG.info(f"驗證碼 [{validate}] 不正確，請重新填寫")
                    continue
                else:
                    LOG.error("unknown response.text!")
                    LOG.error(response.text)
            except BannedIPException as e:
                raise e
            except Exception as e:
                LOG.error(f"unknown Exception : {str(e)}")
                LOG.error(e)

    # 获取验证码
    def get_validate(self):
        random_code = random.uniform(0, 1)
        random_code = round(random_code, 16)
        response = self.session.get(
            f"{CL_HOST}/require/codeimg.php?" + str(random_code),
            headers=generate_headers()
        )
        if response.status_code == 403:
            raise BannedIPException()

        # region sleep time
        # 刷新不要快於 2 秒
        interval_time = random.randint(INTERVAL_TIME_MIN, INTERVAL_TIME_MAX)
        time.sleep(interval_time)
        # endregion

        validate = dddd_ocr.classification(response.content)
        return validate

    # 搜索包含关键字的帖子
    def search_post(self):
        try:
            LOG.info(f"The system has already read [{len(GLOBAL_REPLIED_POST)}] posts.")
            params = {
                'fid': '7',
            }
            response = self.session.get(f'{CL_HOST}/thread0806.php', params=params, headers=generate_headers())
            if response.status_code == 403:
                raise BannedIPException()
            soup = BeautifulSoup(response.text)
            tbody = soup.find(id="tbody")
            for item in tbody.find_all("tr"):
                time = item.find_all("td")[2].text.replace("\n", "\t")
                if not time.__contains__("分鐘"):
                    continue
                a = item.find_all("td")[1].find("a")
                href = a.attrs['href']

                # read.php?tid=5875097
                # htm_data/2308/7/5875097.html
                tid_regex = r"tid=(\d+)|(\d+)\.html"
                codes_list = re.search(tid_regex, href)
                tid = codes_list.group(1) or codes_list.group(2)

                t_title = a.text
                LOG.debug(f"Latest post: \n{time}:{t_title}\n\t>>>> : {CL_HOST}/{href}")
                if FILTER_KEYWORDS and len(FILTER_KEYWORDS) > 0:
                    if not any(key in t_title for key in FILTER_KEYWORDS):
                        LOG.debug(f"Ignore post: Keyword filter >>> \n{time}:{t_title}\n\t>>>> : {CL_HOST}/{href}")
                        continue

                if GLOBAL_REPLIED_POST.__contains__(tid):
                    LOG.debug(f"Ignore post: Already used >>> \n{time}:{t_title}\n\t>>>> : {CL_HOST}/{href}")
                    continue

                GLOBAL_REPLIED_POST.append(tid)
                LOG.info(f"Match a post \n{time}:{t_title}\n\t>>>> : {CL_HOST}/{href}")
                notify_msg(f"Match a post \n{time}:{t_title}\n\t>>>> : {CL_HOST}/{href}")
                codes = self.get_codes_with_href(href)

                if codes and len(codes) > 0:
                    notify_msg(f"codes_with_mask is {codes}\n{CL_HOST}/{href}")
                    return codes
            LOG.info(f"No posts matched with keywords : {FILTER_KEYWORDS} , To be continue.")
        except BannedIPException as e:
            raise e
        except Exception as e:
            LOG.error(f"search_codes unknown ex {str(e)}", e)
        return []

    # 根据帖子内容获取邀请码
    def get_codes_with_href(self, href):
        # href = "htm_data/2306/7/5765077.html"
        response = self.session.get(f'{CL_HOST}/{href}', headers=generate_headers())
        soup = BeautifulSoup(response.text)
        content_node = soup.find(id="conttpc")
        codes_list = re.findall(INVITATION_CODE_REGEX, content_node.text, re.MULTILINE)
        # codes_list = None
        if not codes_list:
            if not IMG_OCR:
                return []
            if not IMG_OCR.get("app_key") or not IMG_OCR.get("secret"):
                return []
            for img in content_node.find_all('img'):
                try:
                    img_url = img.attrs['ess-data'] or img.attrs['src']
                    if not img_url:
                        continue
                    if img_url.endswith(".gif"):
                        continue
                    codes_list.extend(img_codes_by_ocr(img_url))
                except Exception as e:
                    LOG.error(f"Get img src error {str(e)}")
        # codes = [code for code in codes if count_non_alphanumeric(code) <= MASK_COUNT_MAX]
        filter_codes_by_mask_num(codes_list)
        return list(set(codes_list))

    # 使用邀请码注册
    def register_with_real_code(self, code_real):
        while True:
            try:
                validate = self.get_validate()
                data = {
                    'regname': self.user_name,
                    'regpwd': self.password,
                    'regpwdrepeat': self.password,
                    'regemail': self.mail,
                    'invcode': code_real,
                    'validate': validate,
                    'forward': '',
                    'step': '2',
                }
                response = self.session.post(
                    f'{CL_HOST}/register.php?',
                    headers=generate_headers(),
                    data=data
                )
                if response.text.find("恭喜") != -1:
                    LOG.info(response.text)
                    LOG.info(f"恭喜您,完成註冊現在可以開始使用您的會員權利了: {data} ")
                    return True
                elif response.text.find("邀請碼錯誤") != -1:
                    LOG.info(f"邀請碼錯誤: {code_real}")
                    break
                elif response.text.find("驗證碼不正確") != -1:
                    LOG.info(f"驗證碼不正確，請重新填寫: {code_real}:{validate}")
                    continue
                else:
                    LOG.error(f"unknown response.text! {code_real}")
                    LOG.error(response.text)
            except Exception as e:
                LOG.error(f"register_with_code_real error {str(e)}")

        return False

    def check_with_real_code(self, code_real):
        while True:
            validate = self.get_validate()
            data = {
                'reginvcode': code_real,
                'validate': validate,
                'action': 'reginvcodeck',
            }
            response = self.session.post(f'{CL_HOST}/register.php?', headers=generate_headers(), data=data)
            if response.text.find("parent.retmsg_invcode('1')") > -1:
                LOG.info(f"邀請碼 [{code_real}] 不存在或已被使用，您無法注冊！")
                return False

            elif response.text.find("parent.retmsg_invcode('2')") > -1:
                LOG.info(f"驗證碼 [{validate}] 不正確，請重新填寫!")
                continue

            elif response.text.find("parent.retmsg_invcode('0')") > -1:
                LOG.info(f"恭喜您，您可以使用這個邀請碼 [{code_real}] 註冊！")
                break
            else:
                LOG.error(f"unknown response.text! {code_real}")
                LOG.error(response.text)


def img_codes_by_ocr(img_url):
    codes = []
    try:
        app_key = IMG_OCR.get("app_key")
        secret = IMG_OCR.get("secret")

        session = requests.Session()
        session.proxies = PROXY

        response = session.get(img_url)
        q = base64.b64encode(response.content).decode('utf-8')
        data = {
            'detectType': '10012',
            'imageType': '1',
            'langType': 'en',
            'img': q,
            'docType': 'json',
            'signType': 'v3'
        }
        cur_time = str(int(time.time()))
        data['curtime'] = cur_time
        salt = str(uuid.uuid1())

        def truncate(q):
            if q is None:
                return None
            size = len(q)
            return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

        def encrypt(signStr):
            hash_algorithm = hashlib.sha256()
            hash_algorithm.update(signStr.encode('utf-8'))
            return hash_algorithm.hexdigest()

        sign_str = app_key + truncate(q) + salt + cur_time + secret
        sign = encrypt(sign_str)
        data['appKey'] = app_key
        data['salt'] = salt
        data['sign'] = sign
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = session.post("https://openapi.youdao.com/ocrapi", data=data, headers=headers)
        for region in response.json()['Result']['regions']:
            for line in region['lines']:
                for word in line['words']:
                    word = word['word'].replace(" ", "")
                    match = re.match(INVITATION_CODE_REGEX, word)
                    if match:
                        codes.append(match.string)
    except Exception as e:
        LOG.error(f"img_codes_by_ocr error [{img_url}]:{str(e)}")
        LOG.error(e)
    return codes


if __name__ == '__main__':
    # <editor-fold desc="TEST">

    # task = RegisteredTask({"user_name": "yourfirstuser"})
    # task.init_session()
    # task.check_user_status()

    # </editor-fold>

    for registered_user in REGISTERED_USERS:
        RegisteredTask(registered_user).start()
    LOG.info("All over.")
