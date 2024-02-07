from threading import Thread
from DrissionPage import ChromiumPage, ChromiumOptions

def login_process():
    # Configure and instantiate a browser
    co = ChromiumOptions().auto_port()
    # 阻止“自动保存密码”的提示气泡
    co.set_pref('credentials_enable_service', False)

    # 阻止“要恢复页面吗？Chrome未正确关闭”的提示气泡
    co.set_argument('--hide-crash-restore-bubble')

    # 设置无头模式
    co.set_headless()
    path = r'D:\Chrome\Chrome.exe'  # 请改为你电脑内Chrome可执行文件路径
    co.set_browser_path(path).save()

    page = ChromiumPage(co)

    # Navigate to the login page
    page.get('https://cloud3.ir.basware.com/neologinf/login.aspx')
    print(page.title)

    # Input username and password, then click the login button
    txtUname = page.ele('#txtUsername')
    print(txtUname.text)
    txtUname.input('Pingxin Gao')  # Replace with the actual username
    txtPword = page.ele('#txtPasswd')
    print(txtPword.text)

    txtPword.input('Itsudemo2023!')  # Replace with the actual password
    page.ele('#btnLogin').click()
    print('Clicked')


def main(num_browsers):
    threads = []

    for _ in range(num_browsers):
        # Start a new thread for each login process
        thread = Thread(target=login_process)
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

if __name__ == '__main__':
    num_browsers = 1  # Number of browsers to open simultaneously
    main(num_browsers)