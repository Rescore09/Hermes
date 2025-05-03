import requests
import time
import json
import re
import random
import os
import sys
import threading
import queue
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)  
except ImportError:
    print("Installing required package: colorama")
    os.system('pip install colorama')
    from colorama import init, Fore, Back, Style
    init(autoreset=True)

HERMES_LOGO = f"""
{Fore.CYAN}╦ ╦╔═╗╦═╗╔╦╗╔═╗╔═╗{Style.RESET_ALL}  {Fore.YELLOW}⚡{Style.RESET_ALL}
{Fore.CYAN}╠═╣║╣ ╠╦╝║║║║╣ ╚═╗{Style.RESET_ALL}  TikTok Username Monitor
{Fore.CYAN}╩ ╩╚═╝╩╚═╩ ╩╚═╝╚═╝{Style.RESET_ALL}  v1.0.0
"""

class Proxy:
    def __init__(self, ip: str, port: int, username: Optional[str] = None, password: Optional[str] = None):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

    @property
    def proxy_dict(self) -> Dict[str, str]:
        if self.username and self.password:
            return {
                "http": f"http://{self.username}:{self.password}@{self.ip}:{self.port}",
                "https": f"http://{self.username}:{self.password}@{self.ip}:{self.port}"
            }
        return {
            "http": f"http://{self.ip}:{self.port}",
            "https": f"http://{self.ip}:{self.port}"
        }

    def __str__(self) -> str:
        return f"{self.ip}:{self.port}"

class UserAccount:
    def __init__(self, username: str, nickname: str = "", followers: int = 0, 
                 profile_url: str = "", video_url: str = "", 
                 verified: bool = False, discovery_time: datetime = None):
        self.username = username.strip('@') if username else ""
        self.nickname = nickname
        self.followers = followers
        self.profile_url = profile_url or f"https://www.tiktok.com/@{self.username}"
        self.video_url = video_url
        self.verified = verified
        self.discovery_time = discovery_time or datetime.now()

    def __str__(self) -> str:
        return f"@{self.username}"

    def format_details(self) -> str:
        verified_badge = f"{Fore.CYAN}[✓]{Style.RESET_ALL} " if self.verified else ""
        return (
            f"\n  {Fore.GREEN}Username:{Style.RESET_ALL} @{self.username} {verified_badge}\n"
            f"  {Fore.GREEN}Nickname:{Style.RESET_ALL} {self.nickname}\n"
            f"  {Fore.GREEN}Followers:{Style.RESET_ALL} {self.format_number(self.followers)}\n"
            f"  {Fore.GREEN}Profile:{Style.RESET_ALL} {self.profile_url}\n"
            f"  {Fore.GREEN}Discovered:{Style.RESET_ALL} {self.discovery_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    @staticmethod
    def format_number(num: int) -> str:
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        return str(num)

class HermesMonitor:
    def __init__(self):
        self.session = self._create_session()
        self.user_agents = self._load_user_agents()
        self.proxies: List[Proxy] = []
        self.current_proxy_index = 0
        self.found_usernames = set()
        self.found_users: List[UserAccount] = []
        self.target_length = 4  
        self.running = False
        self.save_file = "hermes_found_usernames.json"
        self.stats = {
            "requests": 0,
            "usernames_checked": 0,
            "start_time": None,
            "rate_limited_count": 0
        }
        self.log_queue = queue.Queue()

        self._load_saved_results()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.tiktok.com/',
            'Origin': 'https://www.tiktok.com'
        })
        return session

    def _load_user_agents(self) -> List[str]:
        return [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        ]

    def _rotate_user_agent(self) -> None:
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents)
        })

    def _rotate_proxy(self) -> None:
        if not self.proxies:
            return

        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        proxy = self.proxies[self.current_proxy_index]
        self.session.proxies.update(proxy.proxy_dict)
        self.log(f"Rotated to proxy: {proxy}", level="debug")

    def load_proxies_from_file(self, filename: str) -> None:
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(':')
                if len(parts) == 2:
                    self.proxies.append(Proxy(parts[0], int(parts[1])))
                elif len(parts) == 4:
                    self.proxies.append(Proxy(parts[0], int(parts[1]), parts[2], parts[3]))

            if self.proxies:
                self.log(f"Loaded {len(self.proxies)} proxies", level="info")

                self._rotate_proxy()
        except Exception as e:
            self.log(f"Failed to load proxies: {str(e)}", level="error")

    def _load_saved_results(self) -> None:
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r') as f:
                    data = json.load(f)

                self.found_usernames = set(data.get('usernames', []))
                users_data = data.get('users', [])

                for user_data in users_data:
                    discovery_time = datetime.fromisoformat(user_data.get('discovery_time', 
                                                                     datetime.now().isoformat()))
                    user = UserAccount(
                        username=user_data.get('username', ''),
                        nickname=user_data.get('nickname', ''),
                        followers=user_data.get('followers', 0),
                        profile_url=user_data.get('profile_url', ''),
                        video_url=user_data.get('video_url', ''),
                        verified=user_data.get('verified', False),
                        discovery_time=discovery_time
                    )
                    self.found_users.append(user)

                self.log(f"Loaded {len(self.found_usernames)} previously found usernames", level="info")
        except Exception as e:
            self.log(f"Failed to load saved results: {str(e)}", level="error")

    def _save_results(self) -> None:
        try:
            users_data = []
            for user in self.found_users:
                users_data.append({
                    'username': user.username,
                    'nickname': user.nickname,
                    'followers': user.followers,
                    'profile_url': user.profile_url,
                    'video_url': user.video_url,
                    'verified': user.verified,
                    'discovery_time': user.discovery_time.isoformat()
                })

            data = {
                'usernames': list(self.found_usernames),
                'users': users_data,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.save_file, 'w') as f:
                json.dump(data, f, indent=2)

            self.log(f"Saved {len(self.found_usernames)} usernames to {self.save_file}", level="debug")
        except Exception as e:
            self.log(f"Failed to save results: {str(e)}", level="error")

    def log(self, message: str, level: str = "info") -> None:
        time_str = datetime.now().strftime("%H:%M:%S")

        color_map = {
            "error": Fore.RED,
            "warning": Fore.YELLOW,
            "info": Fore.WHITE,
            "success": Fore.GREEN,
            "debug": Fore.CYAN
        }

        color = color_map.get(level, Fore.WHITE)
        formatted = f"[{time_str}] {color}{message}{Style.RESET_ALL}"
        self.log_queue.put(formatted)

    def is_target_username(self, username: str) -> bool:
        if username.startswith('@'):
            username = username[1:]

        return len(username) == self.target_length and username.isalnum()

    def make_request(self, url: str, params: Dict = None) -> Dict:
        self.stats["requests"] += 1

        try:

            if self.stats["requests"] % 10 == 0:
                self._rotate_user_agent()

            if self.proxies and self.stats["requests"] % 5 == 0:
                self._rotate_proxy()

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 429:
                self.stats["rate_limited_count"] += 1
                self.log("Rate limited by TikTok. Rotating proxy and user agent.", level="warning")
                self._rotate_user_agent()
                if self.proxies:
                    self._rotate_proxy()
                time.sleep(random.uniform(5, 10))
                return {}

            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"Error: Status code {response.status_code}", level="error")
                return {}

        except requests.exceptions.RequestException as e:
            self.log(f"Request error: {str(e)}", level="error")
            if self.proxies:
                self._rotate_proxy()
            return {}
        except json.JSONDecodeError:
            self.log("Error: Invalid JSON response", level="error")
            return {}
        except Exception as e:
            self.log(f"Unexpected error: {str(e)}", level="error")
            return {}

    def get_trending_posts(self) -> List[Dict]:
        url = "https://www.tiktok.com/api/recommend/item_list/"
        params = {
            "aid": "1988",
            "app_language": "en",
            "count": 30,
            "from_page": "fyp"
        }

        data = self.make_request(url, params)
        return data.get('itemList', [])

    def search_by_keyword(self, keyword: str) -> List[Dict]:
        url = "https://www.tiktok.com/api/search/user/full/"
        params = {
            "aid": "1988",
            "app_language": "en",
            "keyword": keyword,
            "count": 30
        }

        data = self.make_request(url, params)
        return data.get('userList', [])

    def search_by_suggested(self) -> List[Dict]:
        url = "https://www.tiktok.com/api/recommend/user/list/"
        params = {
            "aid": "1988",
            "app_language": "en",
            "count": 30
        }

        data = self.make_request(url, params)
        return data.get('userList', [])

    def check_trending_posts(self) -> List[UserAccount]:
        found_users = []
        posts = self.get_trending_posts()

        for post in posts:
            try:
                author = post.get('author', {})
                username = author.get('uniqueId', '')
                self.stats["usernames_checked"] += 1

                if self.is_target_username(username) and username not in self.found_usernames:
                    self.found_usernames.add(username)

                    user = UserAccount(
                        username=username,
                        nickname=author.get('nickname', ''),
                        followers=post.get('authorStats', {}).get('followerCount', 0),
                        video_url=f"https://www.tiktok.com/@{username}/video/{post.get('id', '')}",
                        verified=author.get('verified', False)
                    )

                    found_users.append(user)
                    self.found_users.append(user)
                    self.log(f"Found target username: @{username}", level="success")
            except Exception as e:
                self.log(f"Error processing post: {str(e)}", level="error")

        return found_users

    def check_search_results(self, keyword: str) -> List[UserAccount]:
        found_users = []
        users = self.search_by_keyword(keyword)

        for user_entry in users:
            try:
                user_info = user_entry.get('user', {})
                username = user_info.get('uniqueId', '')
                self.stats["usernames_checked"] += 1

                if self.is_target_username(username) and username not in self.found_usernames:
                    self.found_usernames.add(username)

                    user = UserAccount(
                        username=username,
                        nickname=user_info.get('nickname', ''),
                        followers=user_info.get('followerCount', 0),
                        verified=user_info.get('verified', False)
                    )

                    found_users.append(user)
                    self.found_users.append(user)
                    self.log(f"Found target username: @{username}", level="success")
            except Exception as e:
                self.log(f"Error processing user: {str(e)}", level="error")

        return found_users

    def check_suggested_users(self) -> List[UserAccount]:

        found_users = []
        users = self.search_by_suggested()

        for user_entry in users:
            try:
                username = user_entry.get('uniqueId', '')
                self.stats["usernames_checked"] += 1

                if self.is_target_username(username) and username not in self.found_usernames:
                    self.found_usernames.add(username)

                    user = UserAccount(
                        username=username,
                        nickname=user_entry.get('nickname', ''),
                        followers=user_entry.get('followerCount', 0),
                        verified=user_entry.get('verified', False)
                    )

                    found_users.append(user)
                    self.found_users.append(user)
                    self.log(f"Found target username: @{username}", level="success")
            except Exception as e:
                self.log(f"Error processing suggested user: {str(e)}", level="error")

        return found_users

    def monitor_trending(self, interval: int = 60) -> None:
        self.running = True
        self.stats["start_time"] = datetime.now()

        try:
            while self.running:
                self.log(f"Checking trending posts for {self.target_length}-letter usernames...")

                found = self.check_trending_posts()

                if found:
                    self.log(f"Found {len(found)} new target usernames!", level="success")
                    for user in found:
                        print(user.format_details())
                    self._save_results()

                elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
                req_per_min = (self.stats["requests"] / elapsed) * 60 if elapsed > 0 else 0
                self.log(f"Stats: {self.stats['usernames_checked']} usernames checked, "
                      f"{len(self.found_usernames)} found, "
                      f"{req_per_min:.1f} req/min", level="info")

                sleep_time = random.uniform(interval * 0.8, interval * 1.2)
                self.log(f"Waiting {sleep_time:.1f} seconds before next check...")

                start_time = time.time()
                while time.time() - start_time < sleep_time and self.running:
                    time.sleep(1)

        except KeyboardInterrupt:
            self.log("Monitoring stopped by user", level="warning")
        except Exception as e:
            self.log(f"Error during monitoring: {str(e)}", level="error")
        finally:
            self._save_results()
            self.running = False

    def monitor_with_keywords(self, keywords: List[str], interval: int = 60) -> None:
        self.running = True
        self.stats["start_time"] = datetime.now()

        try:
            while self.running:
                for keyword in keywords:
                    if not self.running:
                        break

                    self.log(f"Searching for '{keyword}'...")
                    found = self.check_search_results(keyword)

                    if found:
                        self.log(f"Found {len(found)} new target usernames for '{keyword}'!", level="success")
                        for user in found:
                            print(user.format_details())
                        self._save_results()

                    time.sleep(random.uniform(5, 10))

                elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
                req_per_min = (self.stats["requests"] / elapsed) * 60 if elapsed > 0 else 0
                self.log(f"Stats: {self.stats['usernames_checked']} usernames checked, "
                      f"{len(self.found_usernames)} found, "
                      f"{req_per_min:.1f} req/min", level="info")

                sleep_time = random.uniform(interval * 0.8, interval * 1.2)
                self.log(f"Waiting {sleep_time:.1f} seconds before next round...")

                start_time = time.time()
                while time.time() - start_time < sleep_time and self.running:
                    time.sleep(1)

        except KeyboardInterrupt:
            self.log("Monitoring stopped by user", level="warning")
        except Exception as e:
            self.log(f"Error during monitoring: {str(e)}", level="error")
        finally:
            self._save_results()
            self.running = False

    def display_logo(self) -> None:
        print(HERMES_LOGO)

    def display_menu(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        self.display_logo()

        print(f"{Fore.CYAN}╔══════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL}           {Fore.YELLOW}HERMES MAIN MENU{Style.RESET_ALL}             {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╠══════════════════════════════════════════╣{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}1.{Style.RESET_ALL} Monitor trending feed continuously    {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}2.{Style.RESET_ALL} Search for usernames by keywords      {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}3.{Style.RESET_ALL} Check suggested users                 {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}4.{Style.RESET_ALL} View found usernames                  {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}5.{Style.RESET_ALL} Change target username length         {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}6.{Style.RESET_ALL} Load proxies                          {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}7.{Style.RESET_ALL} Settings                              {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}0.{Style.RESET_ALL} Exit                                  {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚══════════════════════════════════════════╝{Style.RESET_ALL}")

        print(f"\n{Fore.YELLOW}Current Status:{Style.RESET_ALL}")
        print(f"  Target username length: {Fore.GREEN}{self.target_length}{Style.RESET_ALL} characters")
        print(f"  Found usernames: {Fore.GREEN}{len(self.found_usernames)}{Style.RESET_ALL}")
        print(f"  Active proxies: {Fore.GREEN}{len(self.proxies)}{Style.RESET_ALL}")

        print("\n" + Fore.CYAN + "=" * 50 + Style.RESET_ALL)

    def logger_thread(self) -> None:
        while self.running or not self.log_queue.empty():
            try:

                if not self.log_queue.empty():
                    message = self.log_queue.get(block=False)
                    print(message)
                    self.log_queue.task_done()
                else:
                    time.sleep(0.1)
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                print(f"Logger error: {str(e)}")

    def view_found_usernames(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        self.display_logo()

        print(f"{Fore.CYAN}╔══════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL}          {Fore.YELLOW}FOUND USERNAMES{Style.RESET_ALL}               {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚══════════════════════════════════════════╝{Style.RESET_ALL}")

        if not self.found_users:
            print(f"\n{Fore.YELLOW}No usernames found yet.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}Found {len(self.found_users)} usernames:{Style.RESET_ALL}\n")

            sorted_users = sorted(self.found_users, key=lambda x: x.followers, reverse=True)

            for i, user in enumerate(sorted_users, 1):
                print(f"{Fore.CYAN}{i}.{Style.RESET_ALL}{user.format_details()}")
                print(Fore.CYAN + "-" * 40 + Style.RESET_ALL)

        input(f"\n{Fore.YELLOW}Press Enter to return to the main menu...{Style.RESET_ALL}")

    def change_target_length(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        self.display_logo()

        print(f"{Fore.CYAN}╔══════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL}       {Fore.YELLOW}CHANGE TARGET LENGTH{Style.RESET_ALL}             {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚══════════════════════════════════════════╝{Style.RESET_ALL}")

        print(f"\nCurrent target length: {Fore.GREEN}{self.target_length}{Style.RESET_ALL} characters")

        try:
            new_length = input(f"\nEnter new target length (3-5): {Fore.GREEN}")
            print(Style.RESET_ALL, end="")

            new_length = int(new_length)
            if 3 <= new_length <= 5:
                self.target_length = new_length
                print(f"\n{Fore.GREEN}Target length updated to {self.target_length} characters.{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}Invalid length. Please choose between 3 and 5.{Style.RESET_ALL}")
        except ValueError:
            print(f"\n{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")

        input(f"\n{Fore.YELLOW}Press Enter to return to the main menu...{Style.RESET_ALL}")

    def load_proxies(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        self.display_logo()

        print(f"{Fore.CYAN}╔══════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL}            {Fore.YELLOW}LOAD PROXIES{Style.RESET_ALL}                {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚══════════════════════════════════════════╝{Style.RESET_ALL}")

        print(f"\nCurrent proxies: {Fore.GREEN}{len(self.proxies)}{Style.RESET_ALL}")

        filename = input(f"\nEnter proxy file path (or press Enter to cancel): {Fore.GREEN}")
        print(Style.RESET_ALL, end="")

        if filename:
            if os.path.exists(filename):
                self.proxies = []  
                self.load_proxies_from_file(filename)
                print(f"\n{Fore.GREEN}Successfully loaded {len(self.proxies)} proxies.{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}File not found. Please check the path.{Style.RESET_ALL}")

        input(f"\n{Fore.YELLOW}Press Enter to return to the main menu...{Style.RESET_ALL}")

    def display_settings(self) -> None:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.display_logo()

            print(f"{Fore.CYAN}╔══════════════════════════════════════════╗{Style.RESET_ALL}")
            print(f"{Fore.CYAN}║{Style.RESET_ALL}             {Fore.YELLOW}SETTINGS{Style.RESET_ALL}                    {Fore.CYAN}║{Style.RESET_ALL}")
            print(f"{Fore.CYAN}╠══════════════════════════════════════════╣{Style.RESET_ALL}")
            print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}1.{Style.RESET_ALL} Save file: {self.save_file:<19}     {Fore.CYAN}║{Style.RESET_ALL}")
            print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}2.{Style.RESET_ALL} Target username length: {self.target_length:<10}     {Fore.CYAN}║{Style.RESET_ALL}")
            print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}3.{Style.RESET_ALL} Export found usernames                {Fore.CYAN}║{Style.RESET_ALL}")
            print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}4.{Style.RESET_ALL} Clear found usernames                 {Fore.CYAN}║{Style.RESET_ALL}")
            print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.GREEN}0.{Style.RESET_ALL} Back to main menu                     {Fore.CYAN}║{Style.RESET_ALL}")
            print(f"{Fore.CYAN}╚══════════════════════════════════════════╝{Style.RESET_ALL}")

            choice = input(f"\nEnter your choice (0-4): {Fore.GREEN}")
            print(Style.RESET_ALL, end="")

            if choice == "1":
                new_file = input(f"\nEnter new save file name (current: {self.save_file}): {Fore.GREEN}")
                print(Style.RESET_ALL, end="")
                if new_file:
                    self.save_file = new_file
            elif choice == "2":
                self.change_target_length()
            elif choice == "3":
                self.export_usernames()
            elif choice == "4":
                confirm = input(f"\n{Fore.RED}Are you sure you want to clear all found usernames? (y/n): {Fore.GREEN}")
                print(Style.RESET_ALL, end="")
                if confirm.lower() == 'y':
                    self.found_usernames = set()
                    self.found_users = []
                    print(f"\n{Fore.GREEN}All found usernames have been cleared.{Style.RESET_ALL}")
                    time.sleep(2)
            elif choice == "0":
                break

    def export_usernames(self) -> None:
        try:
            export_file = f"hermes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            with open(export_file, 'w') as f:
                f.write(f"# Hermes TikTok Username Monitor - Export\n")
                f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total usernames: {len(self.found_usernames)}\n\n")

                for user in sorted(self.found_users, key=lambda x: x.followers, reverse=True):
                    f.write(f"@{user.username}\n")
                    f.write(f"Nickname: {user.nickname}\n")
                    f.write(f"Followers: {user.followers}\n")
                    f.write(f"Profile: {user.profile_url}\n")
                    f.write(f"Discovered: {user.discovery_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("-" * 40 + "\n")

            print(f"\n{Fore.GREEN}Successfully exported to {export_file}{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}Export failed: {str(e)}{Style.RESET_ALL}")

        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

    def start(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        self.display_logo()

        print(f"{Fore.YELLOW}Initializing Hermes TikTok Username Monitor...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}=" * 50 + Style.RESET_ALL)
        time.sleep(1)

        while True:
            self.display_menu()

            choice = input(f"\n{Fore.YELLOW}Enter your choice (0-7): {Fore.GREEN}")
            print(Style.RESET_ALL, end="")

            if choice == "1":
                os.system('cls' if os.name == 'nt' else 'clear')
                self.display_logo()

                print(f"{Fore.CYAN}╔══════════════════════════════════════════╗{Style.RESET_ALL}")
                print(f"{Fore.CYAN}║{Style.RESET_ALL}        {Fore.YELLOW}MONITOR TRENDING FEED{Style.RESET_ALL}           {Fore.CYAN}║{Style.RESET_ALL}")
                print(f"{Fore.CYAN}╚══════════════════════════════════════════╝{Style.RESET_ALL}")

                try:
                    interval = int(input(f"\nCheck interval in seconds (default 60): {Fore.GREEN}") or "60")
                    print(Style.RESET_ALL, end="")

                    print(f"\n{Fore.YELLOW}Starting monitor with {interval} second interval.{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}Press Ctrl+C to stop monitoring.{Style.RESET_ALL}\n")

                    self.running = True
                    logger_thread = threading.Thread(target=self.logger_thread)
                    logger_thread.daemon = True
                    logger_thread.start()

                    self.monitor_trending(interval)

                    self.running = False
                    logger_thread.join(timeout=2)

                except ValueError:
                    print(f"\n{Fore.RED}Invalid interval. Using default 60 seconds.{Style.RESET_ALL}")
                    time.sleep(2)

                input(f"\n{Fore.YELLOW}Press Enter to return to the main menu...{Style.RESET_ALL}")

            elif choice == "2":
                os.system('cls' if os.name == 'nt' else 'clear')
                self.display_logo()

                print(f"{Fore.CYAN}╔══════════════════════════════════════════╗{Style.RESET_ALL}")
                print(f"{Fore.CYAN}║{Style.RESET_ALL}          {Fore.YELLOW}KEYWORD SEARCH{Style.RESET_ALL}                {Fore.CYAN}║{Style.RESET_ALL}")
                print(f"{Fore.CYAN}╚══════════════════════════════════════════╝{Style.RESET_ALL}")

                keywords_input = input(f"\nEnter keywords separated by commas: {Fore.GREEN}")
                print(Style.RESET_ALL, end="")

                if keywords_input:
                    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]

                    try:
                        interval = int(input(f"\nCheck interval in seconds (default 120): {Fore.GREEN}") or "120")
                        print(Style.RESET_ALL, end="")

                        print(f"\n{Fore.YELLOW}Starting keyword search with keywords: {', '.join(keywords)}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}Press Ctrl+C to stop monitoring.{Style.RESET_ALL}\n")

                        self.running = True
                        logger_thread = threading.Thread(target=self.logger_thread)
                        logger_thread.daemon = True
                        logger_thread.start()

                        self.monitor_with_keywords(keywords, interval)

                        self.running = False
                        logger_thread.join(timeout=2)

                    except ValueError:
                        print(f"\n{Fore.RED}Invalid interval. Using default 120 seconds.{Style.RESET_ALL}")
                        time.sleep(2)
                else:
                    print(f"\n{Fore.RED}No keywords entered.{Style.RESET_ALL}")
                    time.sleep(2)

                input(f"\n{Fore.YELLOW}Press Enter to return to the main menu...{Style.RESET_ALL}")

            elif choice == "3":
                os.system('cls' if os.name == 'nt' else 'clear')
                self.display_logo()

                print(f"{Fore.CYAN}╔══════════════════════════════════════════╗{Style.RESET_ALL}")
                print(f"{Fore.CYAN}║{Style.RESET_ALL}        {Fore.YELLOW}CHECK SUGGESTED USERS{Style.RESET_ALL}           {Fore.CYAN}║{Style.RESET_ALL}")
                print(f"{Fore.CYAN}╚══════════════════════════════════════════╝{Style.RESET_ALL}")

                print(f"\n{Fore.YELLOW}Checking suggested users...{Style.RESET_ALL}")

                found = self.check_suggested_users()

                if found:
                    print(f"\n{Fore.GREEN}Found {len(found)} new target usernames!{Style.RESET_ALL}")
                    for user in found:
                        print(user.format_details())
                    self._save_results()
                else:
                    print(f"\n{Fore.YELLOW}No new target usernames found.{Style.RESET_ALL}")

                input(f"\n{Fore.YELLOW}Press Enter to return to the main menu...{Style.RESET_ALL}")

            elif choice == "4":
                self.view_found_usernames()

            elif choice == "5":
                self.change_target_length()

            elif choice == "6":
                self.load_proxies()

            elif choice == "7":
                self.display_settings()

            elif choice == "0":
                os.system('cls' if os.name == 'nt' else 'clear')
                self.display_logo()
                print(f"\n{Fore.YELLOW}Thank you for using Hermes TikTok Username Monitor!{Style.RESET_ALL}")
                time.sleep(1)
                break

            else:
                print(f"\n{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
                time.sleep(1)

def main():
    try:

        init(autoreset=True)

        monitor = HermesMonitor()
        monitor.start()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Program terminated by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}An error occurred: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
