from DrissionPage import WebPage, ChromiumOptions, SessionOptions

co = ChromiumOptions()
so = SessionOptions()

page = WebPage(chromium_options=co, session_or_options=so)
# 跳转到登录页面
page.get('https://cloud3.ir.basware.com/neologinf/login.aspx')  # get()方法用于访问参数中的网址。它会等待页面完全加载，再继续执行后面的代码。
txtUname =page.ele('#txtUsername')  # 查找所有拥有 class 属性的元素
txtUname.input('Pingxin Gao') #用户名
txtPword = page.ele('#txtPasswd')
txtPword.input('Itsudemo2023!') #密码
page.ele('#btnLogin').click() #点击登录


# from DrissionPage import WebPage

# # 创建页面对象
# page = WebPage()
# # 访问网址
# page.get('https://search.gitee.com')
# # 查找文本框元素并输入关键词
# page('#search-input').input('test')
# # 点击搜索按钮
# page('text=搜索').click()
# # 等待页面加载
# page.wait.load_start()
# # 切换到收发数据包模式
# page.change_mode()
# # 获取所有行元素
# items = page('#hits-list').eles('.item')
# # 遍历获取到的元素
# for item in items:
#     # 打印元素文本
#     print(item('.title').text)
#     print(item('.desc').text)
#     print()



# from threading import Thread
# from DrissionPage import ChromiumPage, ChromiumOptions
# from DataRecorder import Recorder


# def collect(page, recorder):
#     """用于采集的方法
#     :param page: ChromiumTab 对象
#     :param recorder: Recorder 记录器对象
#     :param title: 类别标题
#     :return: None
#     """
#     num = 1  # 当前采集页数
#     while True:
#         # 遍历所有标题元素
#         items = page('#hits-list').eles('.item')

#         for item in items:
#             # 获取某页所有库名称，记录到记录器
#             recorder.add_data((item('.title').text, item('.desc').text))

#         # 如果有下一页，点击翻页
#         btn = page('text=下一页>', timeout=2)
#         if btn:
#             btn.click(by_js=True)
#             page.wait.load_start()
#             num += 1

#         # 否则，采集完毕
#         else:
#             break


# def main():
#     # 创建两个配置对象，并设置自动分配端口
#     co1 = ChromiumOptions().auto_port()
#     co2 = ChromiumOptions().auto_port()
#     # 新建2个页面对象，各自使用一个配置对象
#     page1 = ChromiumPage(co1)
#     page2 = ChromiumPage(co2)
#     # 第一个浏览器访问第一个网址
#     page1.get('https://search.gitee.com')
#     page1('#search-input').input('Flutter')
#     page1('text=搜索').click()
#     page1.wait.load_start()

#     # 第二个浏览器访问另一个网址
#     page2.get('https://search.gitee.com')
#     page2('#search-input').input('AI')
#     page2('text=搜索').click()
#     page2.wait.load_start()
#     # 新建记录器对象
#     recorder = Recorder('data.csv')

#     # 多线程同时处理多个页面
#     Thread(target=collect, args=(page1, recorder, 'Flutter')).start()
#     Thread(target=collect, args=(page2, recorder, 'AI')).start()


# if __name__ == '__main__':
#     main()


from threading import Thread
from DrissionPage import ChromiumPage, ChromiumOptions
from DataRecorder import Recorder

def collect(page, recorder, search_query):
    """用于采集的方法
    :param page: ChromiumTab 对象
    :param recorder: Recorder 记录器对象
    :param title: 类别标题
    :return: None
    """
    num = 1  # 当前采集页数
    while True:
        # 遍历所有标题元素
        items = page('#hits-list').eles('.item')

        for item in items:
            # 获取某页所有库名称，记录到记录器
            recorder.add_data((search_query, item('.title').text, item('.desc').text))

        # 如果有下一页，点击翻页
        btn = page('text=下一页>', timeout=2)
        if btn:
            btn.click(by_js=True)
            page.wait.load_start()
            num += 1

        # 否则，采集完毕
        else:
            break
def main(num_browsers):
    # Initialize a list to store browser and thread objects
    browsers = []
    threads = []
    search_queries = ['Flutter', 'AI', 'Another Query']  # Example search queries

    # Create a recorder object
    recorder = Recorder('data.csv')

    for i in range(num_browsers):
        # Create browser options and page
        co = ChromiumOptions().auto_port()
        page = ChromiumPage(co)

        # Access search page and perform search with the i-th query
        page.get('https://search.gitee.com')
        search_query = search_queries[i % len(search_queries)]  # Cycle through search queries if fewer than browsers
        page('#search-input').input(search_query)
        page('text=搜索').click()

        # Append browser to the list
        browsers.append(page)

        # Create and start a new thread for each browser
        thread = Thread(target=collect, args=(page, recorder, search_query))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

if __name__ == '__main__':
    num_browsers = 3  # Set the number of browsers you want to use
    main(num_browsers)
