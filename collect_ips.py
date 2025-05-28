import requests
from bs4 import BeautifulSoup
import re
import os

# 目标URL列表
# 现在只包含 https://cf.090227.xyz/，因为这是您明确要求抓取的页面
urls = ['https://cf.090227.xyz/']

# 正则表达式用于匹配IPv4地址
ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'

# 定义User-Agent，模拟浏览器请求，以避免被网站阻止
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 检查ip.txt文件是否存在，如果存在则删除它
if os.path.exists('ip.txt'):
    os.remove('ip.txt')
    print("已删除旧的 ip.txt 文件。")

# 使用集合 (set) 来存储IP地址，集合会自动处理重复项，确保最终IP地址是唯一的
found_ips = set()

# 遍历URL列表
for url in urls:
    print(f"正在从 {url} 获取内容...")
    html_content = None # 初始化为 None
    try:
        # 发送HTTP GET请求获取网页内容，设置请求头和超时时间
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # 如果HTTP响应状态码不是200，则抛出异常
        html_content = response.text # 获取网页的文本内容
        print(f"成功从 {url} 获取HTML内容。")
    except requests.exceptions.Timeout:
        print(f"错误: 从 {url} 获取HTML内容超时（已设置15秒超时）。")
        continue  # 跳过当前URL，继续处理下一个
    except requests.exceptions.RequestException as e:
        print(f"错误: 无法从 {url} 获取HTML内容: {e}")
        continue  # 跳过当前URL，继续处理下一个
    except Exception as e:
        print(f"错误: 从 {url} 获取HTML时发生未知错误: {e}")
        continue  # 跳过当前URL，继续处理下一个

    # 如果成功获取到HTML内容，则进行解析
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        current_url_ips_extracted = 0 # 记录当前URL通过表格解析提取的IP数量

        # === 针对 https://cf.090227.xyz/ 的表格抓取规则 ===
        # 这个逻辑是基于您提供的HTML源码结构
        if url == 'https://cf.090227.xyz/':
            print("尝试使用表格解析规则 (div.centered -> table -> IP列)...")
            try:
                # 查找 class 为 'centered' 的 div 容器
                table_container = soup.find('div', class_='centered')
                # 如果找到容器，则在其内部查找 table 元素
                table = table_container.find('table') if table_container else None

                if table: # 如果表格找到了
                    # 提取表头，用于定位 'IP' 列
                    headers_found = [th.get_text(strip=True) for th in table.find_all('th')]
                    
                    if "IP" in headers_found:
                        ip_column_index = headers_found.index("IP") # 获取 'IP' 列的索引
                        
                        # 遍历表格的所有数据行 (跳过第一个 tr，因为那是表头)
                        for tr in table.find_all('tr')[1:]:
                            tds = tr.find_all('td') # 获取当前行的所有 td 元素
                            
                            # 确保当前行有足够的列来访问IP列
                            if len(tds) > ip_column_index:
                                ip_cell_text = tds[ip_column_index].get_text(strip=True) # 提取IP列的文本
                                # 使用正则表达式从单元格文本中查找所有匹配的IP地址
                                ips = re.findall(ip_pattern, ip_cell_text)
                                for ip in ips:
                                    found_ips.add(ip) # 将找到的IP添加到集合中（自动去重）
                                    current_url_ips_extracted += 1
                        
                        print(f"通过表格解析规则从 {url} 提取了 {current_url_ips_extracted} 个IP地址。")
                        
                        # 如果通过表格解析成功提取到IP，则认为此方法有效，跳过通用回退方案
                        if current_url_ips_extracted > 0:
                            continue # 继续处理下一个URL（如果有的话），这里只有一个URL所以会直接跳出循环
                    else:
                        print(f"警告: 在 {url} 的表格中未找到 'IP' 列。找到的表头: {headers_found}")
                else:
                    print(f"警告: 在 {url} 中未找到 class='centered' 的 div 或其内部的 table。")

            except Exception as e:
                # 捕获表格解析过程中可能发生的任何错误
                print(f"表格解析规则遇到错误: {e}")
        
        # === 回退方案：如果表格解析未找到IP或解析失败，则从整个HTML内容中查找IP ===
        # 这种方法更通用，不依赖于特定的HTML结构，只要IP地址以文本形式存在即可
        # 在此特定场景下（已知HTML结构并已成功解析），这部分通常不会被执行。
        # 但作为安全网，保留它是一个好习惯。
        print(f"回退：从 {url} 的整个HTML内容中查找IP地址...")
        initial_ips_count = len(found_ips) # 记录回退前集合中的IP数量
        
        # 直接对整个HTML内容进行正则匹配，找出所有符合IP模式的字符串
        overall_ips = re.findall(ip_pattern, html_content)
        for ip in overall_ips:
            found_ips.add(ip) # 将所有找到的IP添加到集合中
        
        added_count_by_fallback = len(found_ips) - initial_ips_count # 计算回退方案增加了多少IP
        if added_count_by_fallback > 0:
            print(f"通过回退方案从 {url} 额外提取了 {added_count_by_fallback} 个IP地址。")
        else:
            print(f"回退方案未从 {url} 提取到新的IP地址。")

# 将所有去重后的IP地址写入到ip.txt文件中
# 使用 sorted() 对IP地址进行排序，使输出文件内容更规整
with open('ip.txt', 'w') as file:
    for ip in sorted(list(found_ips)):
        file.write(ip + '\n')

print(f'\n所有去重后的IP地址已成功保存到 ip.txt 文件中，共 {len(found_ips)} 个。')
