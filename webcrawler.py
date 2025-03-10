import requests
import aiohttp
import asyncio
import aiofiles
from requests.exceptions import HTTPError
from urllib.parse import urlparse, urljoin
import os, codecs
from urllib.robotparser import RobotFileParser
from urllib.parse import unquote
import time

class WebCrawler:
    def __init__(self):
        self.keywords = [
                "เชียงราย", "เชียงใหม่", "น่าน", "พะเยา", "แพร่", "แม่ฮ่องสอน", "ลำปาง", "ลำพูน", "อุตรดิตถ์",
                "กำแพงเพชร", "พิจิตร", "พิษณุโลก", "เพชรบูรณ์", "สุโขทัย", "อุทัยธานี", "นครสวรรค์",
                "กาฬสินธุ์", "ขอนแก่น", "ชัยภูมิ", "นครพนม", "นครราชสีมา", "บึงกาฬ", "บุรีรัมย์", "มหาสารคาม",
                "มุกดาหาร", "ยโสธร", "ร้อยเอ็ด", "ศรีสะเกษ", "สกลนคร", "สุรินทร์", "หนองคาย", "หนองบัวลำภู",
                "อำนาจเจริญ", "อุดรธานี", "อุบลราชธานี", "กาญจนบุรี", "นครปฐม", "ประจวบคีรีขันธ์", "เพชรบุรี",
                "ราชบุรี", "สมุทรสงคราม", "สมุทรสาคร", "สุพรรณบุรี", "จันทบุรี", "ฉะเชิงเทรา", "ชลบุรี", "ตราด",
                "ปราจีนบุรี", "ระยอง", "สระแก้ว", "กรุงเทพ", "นครนายก", "นนทบุรี", "ปทุมธานี", "พระนครศรีอยุธยา",
                "สมุทรปราการ", "สระบุรี", "อ่างทอง", "ชัยนาท", "ลพบุรี", "นครศรีธรรมราช", "กระบี่", "ชุมพร",
                "ตรัง", "นครศรีธรรมราช", "นราธิวาส", "ปัตตานี", "พังงา", "พัทลุง", "ภูเก็ต", "ยะลา", "ระนอง",
                "สงขลา", "สตูล", "สุราษฎร์ธานี", "ไทย", "thai", "เกาะล้าน", "ภูเก็ต"
            ]
        self.non_keywords = [
            "ญี่ปุ่น", "เกาหลี", "จีน", "ฮ่องกง", "ไต้หวัน",
            "สิงคโปร์", "มาเลเซีย", "เวียดนาม", "อินโดนีเซีย", "ฟิลิปปินส์",
            "ฝรั่งเศส", "สหราชอาณาจักร", "เยอรมนี", "อิตาลี", "สวิตเซอร์แลนด์",
            "ออสเตรเลีย", "อเมริกา", "แคนาดา", "นิวซีแลนด์", "นอร์เวย์", "ฟินแลนด์",
            "สวิตเซอร์แลนด์", "สวีเดน", "เดนมาร์ก"
        ]

        self.visited_q = []
        self.have_robots = []
        self.robot_now = ''
        self.is_continue = False
        self.POOL_SIZE = 5
        self.visited_web = []
        self.seed_url = [
                'https://www.lopburi.org/',
                'https://thai.tourismthailand.org/',
                'https://patiew.com/',
                'https://paapaii.com',
                'https://travel.kapook.com/',
                'http://blog.unseentourthailand.com/',
                'https://www.9mot.com/',
                'https://www.sanook.com/travel/',
                'https://travel.trueid.net/',
                'https://chillpainai.com/',
                'https://travelismylifeblog.blogspot.com/',
                'https://www.checkinchill.com/',
        ]
        self.rp = [RobotFileParser() for _ in range(len(self.seed_url))]
        self.frontier_q = [[url] for url in self.seed_url]  # Each index contains a list with a single seed URL
        self.is_done = [False] * len(self.seed_url)  # List of boolean values
        self.wanted_list = ['htm', 'html', 'robots.txt']

        self.current_web = ''

        self.headers = {
            'User-Agent': 'panyawat krongkitichu',
            'From': 'panyawat.kr@ku.th'
        }

        self.count = 1
#end region
#region get_page
    async def get_page(self, url, session):
        """Fetch a page asynchronously"""
        try:
            async with session.get(url, headers=self.headers, timeout=40) as response:
                print(f"{self.count} Fetching {url}")
                response.raise_for_status()
                # text = await response.text()
                # print(text)
                return await response.text()
        except Exception as e:
            print(f"Failed {url}: {e}")
            return ''
    #region link_parser
    def link_parser(self, raw_html):
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
    def enqueue(self, link, seed_order):
        if (link not in self.frontier_q and link not in self.visited_q):
            # print(f'==>{seed_order}')
            self.frontier_q[seed_order].append(link)

    # FIFO queue
    def dequeue(self, seed_order):
        current_url = self.frontier_q[seed_order][0]
        self.frontier_q[seed_order] = self.frontier_q[seed_order][1:]
        return current_url

    def sanitize_path(self, path):
        return path.replace(":", "/")
    #region is_invalid
    def is_invalid(self, url):
        is_inseed = False
        check_url = url.netloc + url.path
        for seed in self.seed_url:
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
    async def save_file(self, html, url):
        parsed_url = urlparse(url)
        path = 'html/' + parsed_url.netloc + parsed_url.path
        path = self.sanitize_path(path)
        
        try:
            if(parsed_url.path.find(".htm") != -1 or parsed_url.path.find(".html") != -1 or parsed_url.path.find("robots.txt") != -1):
                os.makedirs("/".join(path.split('/')[0:-1]), 0o755, exist_ok=True)
                abs_file = path
            else:
                os.makedirs(path, 0o755, exist_ok=True)
                abs_file = path + '/dummy'
            
            async with aiofiles.open(abs_file, 'w', encoding='utf-8') as f:
                await f.write(html)
            self.count += 1
        except:
            return 0
        
        
    #region link op
    def link_op(self, url, parent_url):

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
    async def check_robot(self, url, seed_order):      
        parsed_url = urlparse(url)
        base_url = parsed_url.scheme + '://' + parsed_url.netloc
        robot = base_url + "/robots.txt"
        
        print(f"Check Robot===>{robot}")
        self.robot_now = parsed_url.netloc
        self.rp[seed_order].set_url(robot)
        self.rp[seed_order].read()

        self.visited_q.append(robot)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=40) as response:
                    print(f"{self.count} Fetching {url}")
                    response.raise_for_status()
                    raw = await response.text()
                    return raw
        except Exception as e:
            print(f"Failed {url}: {e}")
            return ''
            
        self.visited_web.append(parsed_url.netloc)
        await self.save_file(raw, robot)
        self.count -= 1
        f = codecs.open('list_robots.txt', 'a', 'utf-8')
        f.write(f'{parsed_url.netloc}\n')
        self.have_robots.append(parsed_url.netloc)
    #region remove substring
    def remove_all_substrings(self, text, start_marker, end_marker):
        while start_marker in text and end_marker in text:
            start = text.find(start_marker)
            end = text.find(end_marker, start + len(start_marker))

            if start == -1 or end == -1:
                break

            text = text[:start] + text[end + len(end_marker):]
        
        return text
    #region remove_list
    def remove_list(self, text):
        text = self.remove_all_substrings(text, '<footer', '</footer>')
        text = self.remove_all_substrings(text, '<aside', '</aside>')
        text = self.remove_all_substrings(text, '<nav', '</nav>')
        return text

    def check_keyword(self, raw_html):
        max_count = 0
        keyword_counts = {key: raw_html.count(key) for key in self.keywords if key in raw_html}
        non_keyword_counts = {key: raw_html.count(key) for key in self.non_keywords if key in raw_html}
        # print(keyword_counts)
        # print(non_keyword_counts)
        for k,v in keyword_counts.items():
            if v > max_count:
                max_count = v
        for k,v in non_keyword_counts.items():
            if v > max_count:
                max_count = v
                return False
        return True


    #region crawl
    async def crawl(self, session, current_url, seed_order):
        # print(f'------------{current_url}')
        
        f = codecs.open('visited_q.txt', 'a', 'utf-8')
        f.write(f'{current_url}\n')
        web = urlparse(current_url).netloc
        # print(can_check)
        # print(f"{self.rp.last_checked}")
        if(not self.rp[seed_order].can_fetch("panyawat krongkitichu", current_url)):
            print(f'block_by_robot===>{current_url}')
            self.visited_q.append(current_url)
        elif(current_url not in self.frontier_q and current_url not in self.visited_q):
            raw_html = await self.get_page(current_url, session)
            extracted_links = self.link_parser(raw_html)
            raw_html = self.remove_list(raw_html)
            # print(raw_html)
            if self.check_keyword(raw_html):
                await self.save_file(raw_html, current_url)
            else:
                print(f'Skipping {current_url} (not relevant)')
            self.visited_q.append(current_url)
            
            # print(extracted_links)
            links = []
            for link in extracted_links:
                # print(link)
                full_url = self.link_op(link, current_url)
                # print(full_url)
                if (self.is_invalid(urlparse(full_url))):
                    # print(f'invalid===>{full_url}')
                    print('',end='')
                else:
                    self.enqueue(full_url, seed_order)
            # print(self.frontier_q)
    #region start
    async def main(self):
        seed_order = 0
        # if (self.is_continue):
        #     f = codecs.open('visited_q.txt', 'r', 'utf-8')
        #     f = f.read()
        #     visited_q = f.strip().split('\n')
        for i in range(len(self.seed_url)):
            await self.check_robot(self.seed_url[i], i)
        tasks = {i: set() for i in range(len(self.seed_url))}
        async with aiohttp.ClientSession() as session:
            while True:
                # print(seed_order)
                # time.sleep(1)
                while len(tasks[seed_order]) < self.POOL_SIZE and self.frontier_q[seed_order]:
                    # time.sleep(0.05)
                    url = self.dequeue(seed_order)
                    task = asyncio.create_task(self.crawl(session, url, seed_order))
                    tasks[seed_order].add(task)
                    # print(self.frontier_q)
                try:
                    done, pending = await asyncio.wait(tasks[seed_order], return_when=asyncio.FIRST_COMPLETED)
                except:
                    if(not self.frontier_q[seed_order]):
                        print(f'endof===>{self.seed_url[seed_order]}')
                        self.is_done[seed_order] = True

                tasks[seed_order].difference_update(done)

                if(seed_order < len(self.seed_url)-1):
                    seed_order += 1
                else:
                    task.add_done_callback(tasks[seed_order].discard)
                    
                    seed_order = 0
                if all(self.is_done):
                    return

            
#endregion
if __name__ == "__main__":
    crawler = WebCrawler()
    asyncio.run(crawler.main())