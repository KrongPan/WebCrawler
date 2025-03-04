import requests
import aiohttp
import asyncio
import aiofiles
from requests.exceptions import HTTPError
from urllib.parse import urlparse, urljoin
import os, codecs
from urllib.robotparser import RobotFileParser
from urllib.parse import unquote

rp = RobotFileParser()

keywords = [
        "เชียงราย", "เชียงใหม่", "น่าน", "พะเยา", "แพร่", "แม่ฮ่องสอน", "ลำปาง", "ลำพูน", "อุตรดิตถ์",
        "กำแพงเพชร", "พิจิตร", "พิษณุโลก", "เพชรบูรณ์", "สุโขทัย", "อุทัยธานี", "นครสวรรค์",
        "กาฬสินธุ์", "ขอนแก่น", "ชัยภูมิ", "นครพนม", "นครราชสีมา", "บึงกาฬ", "บุรีรัมย์", "มหาสารคาม",
        "มุกดาหาร", "ยโสธร", "ร้อยเอ็ด", "ศรีสะเกษ", "สกลนคร", "สุรินทร์", "หนองคาย", "หนองบัวลำภู",
        "อำนาจเจริญ", "อุดรธานี", "อุบลราชธานี", "กาญจนบุรี", "นครปฐม", "ประจวบคีรีขันธ์", "เพชรบุรี",
        "ราชบุรี", "สมุทรสงคราม", "สมุทรสาคร", "สุพรรณบุรี", "จันทบุรี", "ฉะเชิงเทรา", "ชลบุรี", "ตราด",
        "ปราจีนบุรี", "ระยอง", "สระแก้ว", "กรุงเทพ", "นครนายก", "นนทบุรี", "ปทุมธานี", "พระนครศรีอยุธยา",
        "สมุทรปราการ", "สระบุรี", "อ่างทอง", "ชัยนาท", "ลพบุรี", "นครศรีธรรมราช", "กระบี่", "ชุมพร",
        "ตรัง", "นครศรีธรรมราช", "นราธิวาส", "ปัตตานี", "พังงา", "พัทลุง", "ภูเก็ต", "ยะลา", "ระนอง",
        "สงขลา", "สตูล", "สุราษฎร์ธานี"
    ]

visited_q = []
visited_web = []
have_robots = []
robot_now = ''
count = 0
is_continue = False
POOL_SIZE = 20

seed_url = [
            'https://www.lopburi.org/',
            'https://thai.tourismthailand.org/',
            'https://patiew.com/',
            'https://paapaii.com',
            'https://travel.kapook.com/',
            'http://blog.unseentourthailand.com/',
            'https://www.9mot.com/',
            'https://www.gothaitogether.com/',
            'https://www.sanook.com/travel/thailand/',
            'https://www.thairath.co.th/lifestyle/travel/',
            'https://travel.trueid.net/',
]
frontier_q = [seed_url[0]]

wanted_list = ['htm', 'html', 'robots.txt']

current_web = ''

headers = {
    'User-Agent': 'panyawat krongkitichu',
    'From': 'panyawat.kr@ku.th'
}

count = 1
#region get_page
async def get_page(url, session):
    """Fetch a page asynchronously"""
    try:
        async with session.get(url, headers=headers, timeout=40) as response:
            print(f"{count} Fetching {url}")
            response.raise_for_status()
            # text = await response.text()
            # print(text)
            return await response.text()
    except Exception as e:
        print(f"Failed {url}: {e}")
        return ''
#region link_parser
def link_parser(raw_html):
    urls = []
    pattern_start = '<a href="';  pattern_end = '"'
    index = 0;  length = len(raw_html)
    while index < length:
        start = raw_html.find(pattern_start, index)
        if start > 0:
            start = start + len(pattern_start)
            end = raw_html.find(pattern_end, start)
            link = raw_html[start:end]
            if len(link) > 0:
                if link not in urls:
                    urls.append(link)
            index = end
        else:
            break
    
    # print(urls)
    return urls

# param 'links' is a list of extracted links to be stored in the queue
def enqueue(link):
    global frontier_q

    if link not in frontier_q and link not in visited_q:
        frontier_q.append(link)

# FIFO queue
def dequeue():
    global frontier_q
    current_url = frontier_q[0]
    frontier_q = frontier_q[1:]
    return current_url

def sanitize_path(path):
    return path.replace(":", "/")
#region is_invalid
def is_invalid(url):
    global seed_url
    is_inseed = False
    check_url = url.netloc + url.path
    for seed in seed_url:
        if(check_url.find(urlparse(seed).netloc + urlparse(seed).path) != -1):
            is_inseed = True
            break
    if(not is_inseed):
        # print(check_url)
        # print("not in seed")
        return True
    file_type = url.path.split('/')[-1]
    if(file_type.find('.') == -1):
        return False
    if(file_type == "robots.txt"):
        return False
    file_type = file_type.split('.')[-1]
    if(file_type == "htm" or file_type == "html"):
        return False
    return True
#region save_file
async def save_file(html, url):
    global count
        
    parsed_url = urlparse(url)
    path = 'html/' + parsed_url.netloc + parsed_url.path
    path = sanitize_path(path)
    
    try:
        if(parsed_url.path.find(".htm") != -1 or parsed_url.path.find(".html") != -1 or parsed_url.path.find("robots.txt") != -1):
            os.makedirs("/".join(path.split('/')[0:-1]), 0o755, exist_ok=True)
            abs_file = path
        else:
            os.makedirs(path, 0o755, exist_ok=True)
            abs_file = path + '/dummy'
        
        async with aiofiles.open(abs_file, 'w', encoding='utf-8') as f:
            await f.write(html)
        count += 1
    except:
        return 0
    
    
#region link op
def link_op(url, parent_url):
    global seed_url
    # print(url)
    parsed_url = urlparse(url)
    
    if(parsed_url.netloc == ''):
        parent_parsed_url = urlparse(parent_url)
        base_url = parent_parsed_url.scheme + '://' + parent_parsed_url.netloc
    else:
        base_url = parsed_url.scheme + '://' + parsed_url.netloc
    # print(base_url)
    # print(parsed_url)
    link = urljoin(base_url, parsed_url.path.strip().strip('/'))
    link = unquote(link)
    # print(link)
    return link
#region check_robot
async def check_robot(url, session):
    global rp
    global count 
    global current_web
    global robot_now
    parsed_url = urlparse(url)
    base_url = parsed_url.scheme + '://' + parsed_url.netloc
    robot = base_url + "/robots.txt"
    
    if(parsed_url.netloc != current_web):
        if (parsed_url.netloc == robot_now):
            return False
        print(f"Check Robot===>{robot}")
        robot_now = parsed_url.netloc
        rp = RobotFileParser()
        rp.set_url(robot)
        rp.read()

        visited_q.append(robot)
        raw = await get_page(robot,session)
        
        if(raw == ''):
            current_web = parsed_url.netloc
            return False
        current_web = parsed_url.netloc
        if(parsed_url.netloc not in visited_web):
            visited_web.append(parsed_url.netloc)
            await save_file(raw, robot)
            count -= 1
            f = codecs.open('list_robots.txt', 'a', 'utf-8')
            f.write(f'{parsed_url.netloc}\n')
            have_robots.append(parsed_url.netloc)
    else:
        return False
#region remove substring
def remove_all_substrings(text, start_marker, end_marker):
    while start_marker in text and end_marker in text:
        start = text.find(start_marker)
        end = text.find(end_marker, start + len(start_marker))

        if start == -1 or end == -1:
            break

        text = text[:start] + text[end + len(end_marker):]
    
    return text
#region remove_list
def remove_list(text):
    text = remove_all_substrings(text, '<footer', '</footer>')
    text = remove_all_substrings(text, '<aside', '</aside>')
    text = remove_all_substrings(text, '<nav', '</nav>')
    return text
#region crawl
async def crawl(session, current_url):
    global keywords
    # print(f'------------{current_url}')
    
    f = codecs.open('visited_q.txt', 'a', 'utf-8')
    f.write(f'{current_url}\n')
    web = urlparse(current_url).netloc
    can_check = await check_robot(current_url, session)
    # print(can_check)
    # print(f"{rp.last_checked}")
    if(not rp.can_fetch("panyawat krongkitichu", current_url)):
        print(f'block_by_robot===>{current_url}')
        visited_q.append(current_url)
        return False

    

    raw_html = await get_page(current_url, session)
    extracted_links = link_parser(raw_html)
    raw_html = remove_list(raw_html)
    # print(raw_html)
    if any(keyword in raw_html for keyword in keywords):
        await save_file(raw_html, current_url)
    else:
        print(f'Skipping {current_url} (not relevant)')
    visited_q.append(current_url)
    
    # print(extracted_links)
    links = []
    for link in extracted_links:
        # print(link)
        full_url = link_op(link, current_url)
        # print(full_url)
        if (is_invalid(urlparse(full_url))):
            print(f'invalid===>{full_url}')
            return
        else:
            enqueue(full_url)
    # print(frontier_q)
#region start
async def main():
    global visited_q
    seed_count = 0
    # if (is_continue):
    #     f = codecs.open('visited_q.txt', 'r', 'utf-8')
    #     f = f.read()
    #     visited_q = f.strip().split('\n')
    
    async with aiohttp.ClientSession() as session:
        tasks = set()
        while True:
            
            while len(tasks) < POOL_SIZE and frontier_q:
                url = dequeue()
                task = asyncio.create_task(crawl(session, url))
                tasks.add(task)
                # print(frontier_q)

            try:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            except:
                if(frontier_q):
                    continue
                else:
                    seed_count+=1
                    if(seed_count < len(seed_url)):
                      frontier_q.append(seed_url[seed_count])
                      continue
                    else:
                        return

            tasks.difference_update(done)
            
#endregion
asyncio.run(main())