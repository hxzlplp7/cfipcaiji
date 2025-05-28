import requests
from bs4 import BeautifulSoup
import re
import os

# 目标URL列表
# 现在只包含 https://cf.090227.xyz/，因为这是您明确要求抓取的页面
urls = ['https://cf.090227.xyz/']

# 正则表达式用于匹配IPv4地址
# 这是一个用于匹配 IPv4 地址的常见正则表达式，确保即使单元格有额外内容也能提取出IP
ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'

# 定义User-Agent，模拟浏览器请求，以避免被网站阻止
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 检查ip.txt文件是否存在，如果存在则删除它
if os.path.exists('ip.txt'):
    os.remove('ip.txt')
    print("已删除旧的 ip.txt 文件。")

# 使用集合 (set) 来存储格式化后的字符串，集合会自动处理重复项，确保最终输出的行是唯一的
found_formatted_data = set()

# 遍历URL列表 (在这个例子中，只有一个URL)
for url in urls:
    print(f"正在从 {url} 获取内容...")
    html_content = None # 初始化为 None
    try:
        # 发送HTTP GET请求获取网页内容，设置请求头和超时时间
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # 如果HTTP响应状态码不是2xx，则抛出异常
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
        
        # === 针对 https://cf.090227.xyz/ 的表格抓取规则 ===
        print("尝试使用表格解析规则 (div.centered -> table -> 线路, IP, 速度列)...")
        try:
            # 查找 class 为 'centered' 的 div 容器
            table_container = soup.find('div', class_='centered')
            # 如果找到容器，则在其内部查找 table 元素
            table = table_container.find('table') if table_container else None

            if table: # 如果表格找到了
                # 提取表头，用于定位 '线路', 'IP', '速度' 列
                headers_found = [th.get_text(strip=True) for th in table.find_all('th')]
                
                # 定义我们需要获取的列名
                required_columns = ["线路", "IP", "速度"]
                
                # 检查所有必需的列是否存在
                missing_columns = [col for col in required_columns if col not in headers_found]
                
                if missing_columns:
                    print(f"错误: 在 {url} 的表格中未找到以下必需列: {missing_columns}。找到的表头: {headers_found}")
                    continue # 跳过此URL的进一步处理
                
                # 获取所需列的索引
                line_column_index = headers_found.index("线路")
                ip_column_index = headers_found.index("IP")
                speed_column_index = headers_found.index("速度")
                
                print(f"线路列索引: {line_column_index}, IP列索引: {ip_column_index}, 速度列索引: {speed_column_index}")

                extracted_rows_count = 0
                # 遍历表格的所有数据行 (跳过第一个 tr，因为那是表头)
                for tr in table.find_all('tr')[1:]:
                    tds = tr.find_all('td') # 获取当前行的所有 td 元素
                    
                    # 确保当前行有足够的列来访问所有需要的索引
                    # max() 确保即使列顺序变化，也能判断是否有足够的列
                    if len(tds) > max(line_column_index, ip_column_index, speed_column_index):
                        line_text = tds[line_column_index].get_text(strip=True)
                        ip_cell_text = tds[ip_column_index].get_text(strip=True)
                        speed_text = tds[speed_column_index].get_text(strip=True)
                        
                        # 使用正则表达式从IP单元格文本中精确匹配IP地址
                        ip_matches = re.findall(ip_pattern, ip_cell_text)
                        
                        if ip_matches:
                            # 通常一个单元格只会有一个IP，我们取第一个
                            actual_ip = ip_matches[0]
                            # 格式化字符串为 "IP#线路#速度" 格式
                            formatted_line_data = f"{actual_ip}#{line_text}#{speed_text}"
                            found_formatted_data.add(formatted_line_data) # 添加到集合中（自动去重）
                            extracted_rows_count += 1
                        else:
                            print(f"警告: 在行中IP列 '{ip_cell_text}' 未找到有效的IP地址，跳过此行。")
                    else:
                        print(f"警告: 发现行数据列数不足，跳过此行。所需列数：{max(line_column_index, ip_column_index, speed_column_index) + 1}，实际：{len(tds)}。")

                print(f"从 {url} 成功提取并处理了 {extracted_rows_count} 行数据。")

            else:
                print(f"警告: 在 {url} 中未找到 class='centered' 的 div 或其内部的 table。请检查网页结构是否已变化。")

        except Exception as e:
            # 捕获表格解析过程中可能发生的任何错误
            print(f"表格解析规则遇到错误: {e}")
            # 如果需要，可以在这里添加一个通用回退方案，比如从整个HTML文本中查找IP，
            # 但鉴于您提供了明确的HTML结构，我们假设表格是主要的IP来源。

# 将所有去重后的格式化数据写入到ip.txt文件中
# 使用 sorted() 对结果进行排序，使输出文件内容更规整
with open('ip.txt', 'w') as file:
    for data_line in sorted(list(found_formatted_data)):
        file.write(data_line + '\n')

print(f'\n所有去重后的格式化IP信息已成功保存到 ip.txt 文件中，共 {len(found_formatted_data)} 条。')
