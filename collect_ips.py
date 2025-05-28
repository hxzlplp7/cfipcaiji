import requests
from bs4 import BeautifulSoup
import re
import os

# 目标URL列表
# 这里的urls列表只包含 https://ip.164746.xyz，因为它指定了新的抓取规则
urls = ['https://ip.164746.xyz']

# 正则表达式用于匹配IP地址
ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'

# 定义User-Agent，模拟浏览器请求，以避免被网站阻止
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 检查ip.txt文件是否存在，如果存在则删除它
if os.path.exists('ip.txt'):
    os.remove('ip.txt')
    print("已删除旧的 ip.txt 文件。")

# 创建一个文件来存储IP地址
with open('ip.txt', 'w') as file:
    for url in urls:
        print(f"正在从 {url} 获取内容...")
        try:
            # 发送HTTP请求获取网页内容，并设置User-Agent和超时
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()  # 检查HTTP响应状态码，如果不是200则抛出异常
            html_content = response.text
            print(f"成功从 {url} 获取HTML内容，正在解析...")
        except requests.exceptions.Timeout:
            print(f"错误: 从 {url} 获取HTML内容超时（已设置15秒超时）。")
            continue  # 跳过当前URL，处理下一个
        except requests.exceptions.RequestException as e:
            print(f"错误: 无法从 {url} 获取HTML内容: {e}")
            continue  # 跳过当前URL，处理下一个
        except Exception as e:
            print(f"错误: 从 {url} 获取HTML时发生未知错误: {e}")
            continue  # 跳过当前URL，处理下一个

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # === 针对 https://ip.164746.xyz 的新抓取规则 ===
        if url == 'https://ip.164746.xyz':
            try:
                # 查找class为 'centered' 的 div 容器
                table_container = soup.find('div', class_='centered')
                if not table_container:
                    print(f"错误: 未在 {url} 找到class为 'centered' 的 div 容器。")
                    continue

                # 在找到的 div 容器中查找表格
                table = table_container.find('table')
                if not table:
                    print(f"错误: 未在 'centered' div 中找到表格。")
                    continue

                # 提取表头以找到 'IP' 列的索引
                headers_found = [th.get_text(strip=True) for th in table.find_all('th')]
                if "IP" not in headers_found:
                    print(f"错误: 未在 {url} 的表格中找到 'IP' 列。找到的表头有: {headers_found}")
                    continue

                ip_column_index = headers_found.index("IP")
                print(f"IP 列在索引 {ip_column_index}。")

                # 遍历所有数据行 (跳过表头行，即从第二个 <tr> 开始)
                extracted_ip_count = 0
                for tr in table.find_all('tr')[1:]:
                    tds = tr.find_all('td')
                    if len(tds) > ip_column_index: # 确保当前行有足够的列
                        ip_cell_text = tds[ip_column_index].get_text(strip=True)
                        ip_matches = re.findall(ip_pattern, ip_cell_text)

                        for ip in ip_matches:
                            file.write(ip + '\n')
                            extracted_ip_count += 1
                print(f"从 {url} 成功提取并写入了 {extracted_ip_count} 个IP地址。")

            except Exception as e:
                print(f"错误: 解析 {url} 的表格时发生错误: {e}")
                continue
        else:
            # 如果将来urls列表中包含其他网址，并且它们不是 https://ip.164746.xyz，
            # 则可以使用原始的泛化查找所有<tr>元素的逻辑。
            # 当前的urls列表中只有 https://ip.164746.xyz，所以这部分代码暂时不会执行。
            print(f"警告: {url} 未知，使用通用解析规则。")
            elements = soup.find_all('tr') # 原始代码逻辑
            for element in elements:
                element_text = element.get_text()
                ip_matches = re.findall(ip_pattern, element_text)
                for ip in ip_matches:
                    file.write(ip + '\n')

print('所有IP地址已保存到ip.txt文件中。')
