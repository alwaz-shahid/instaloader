import os
import sys
from argparse import ArgumentTypeError

from typing import List, Optional

from enum import IntEnum
from instaloader import (
    AbortDownloadException,
    BadCredentialsException,
    Instaloader,
    InstaloaderException,
    InvalidArgumentException,
    LoginException,
    Post,
    Profile,
    ProfileNotExistsException,
    StoryItem,
    TwoFactorAuthRequiredException,
    load_structure_from_file,
)
from instaloader.instaloader import get_default_session_filename, get_default_stamps_filename
from instaloader.instaloadercontext import default_user_agent
from instaloader.lateststamps import LatestStamps

try:
    import browser_cookie3

    bc3_library = True
except ImportError:
    bc3_library = False


class ExitCode(IntEnum):
    SUCCESS = 0
    NON_FATAL_ERROR = 1
    INIT_FAILURE = 2
    LOGIN_FAILURE = 3
    DOWNLOAD_ABORTED = 4
    USER_ABORTED = 5
    UNEXPECTED_ERROR = 99


class InstagramLoader:
    def __init__(self):
        """Initialize the Instagram loader."""
        self.loader = Instaloader()

    def login(self, username: str, password: str) -> bool:
        """
        Log in to Instagram.

        Args:
            username (str): Instagram username.
            password (str): Instagram password.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        try:
            self.loader.login(username, password)
            return True
        except (BadCredentialsException, TwoFactorAuthRequiredException, LoginException) as e:
            print(f"Login failed: {e}", file=sys.stderr)
            return False

    def load_session_from_browser(self, browser: str, cookiefile: Optional[str] = None) -> bool:
        """
        Load session cookies from a browser.

        Args:
            browser (str): Browser name (e.g., "chrome", "firefox").
            cookiefile (Optional[str]): Path to the cookie file.

        Returns:
            bool: True if cookies are loaded successfully, False otherwise.
        """
        if not bc3_library:
            print("browser_cookie3 library is required to load cookies from browsers.", file=sys.stderr)
            return False

        try:
            cookies = self._get_cookies_from_browser(browser, cookiefile)
            self.loader.context.update_cookies(cookies)
            username = self.loader.test_login()
            if username:
                self.loader.context.username = username
                print(f"Logged in as {username} using cookies from {browser}.")
                return True
            else:
                print("Failed to log in using cookies.", file=sys.stderr)
                return False
        except Exception as e:
            print(f"Failed to load cookies: {e}", file=sys.stderr)
            return False

    def _get_cookies_from_browser(self, browser: str, cookiefile: Optional[str] = None) -> dict:
        """
        Retrieve cookies from a browser.

        Args:
            browser (str): Browser name.
            cookiefile (Optional[str]): Path to the cookie file.

        Returns:
            dict: Dictionary of cookies.
        """
        supported_browsers = {
            "brave": browser_cookie3.brave,
            "chrome": browser_cookie3.chrome,
            "chromium": browser_cookie3.chromium,
            "edge": browser_cookie3.edge,
            "firefox": browser_cookie3.firefox,
            "librewolf": browser_cookie3.librewolf,
            "opera": browser_cookie3.opera,
            "opera_gx": browser_cookie3.opera_gx,
            "safari": browser_cookie3.safari,
            "vivaldi": browser_cookie3.vivaldi,
        }

        if browser not in supported_browsers:
            raise InvalidArgumentException(f"Unsupported browser: {browser}")

        cookies = {}
        browser_cookies = list(supported_browsers[browser](cookie_file=cookiefile))
        for cookie in browser_cookies:
            if "instagram.com" in cookie.domain:
                cookies[cookie.name] = cookie.value

        if not cookies:
            raise LoginException(f"No Instagram cookies found in {browser}.")

        return cookies

    def download_profile(
        self,
        profile_name: str,
        download_posts: bool = True,
        download_stories: bool = False,
        download_highlights: bool = False,
        download_tagged: bool = False,
        download_reels: bool = False,
        download_igtv: bool = False,
        fast_update: bool = False,
    ) -> bool:
        """
        Download content from a profile.

        Args:
            profile_name (str): Instagram profile name.
            download_posts (bool): Whether to download posts.
            download_stories (bool): Whether to download stories.
            download_highlights (bool): Whether to download highlights.
            download_tagged (bool): Whether to download tagged posts.
            download_reels (bool): Whether to download reels.
            download_igtv (bool): Whether to download IGTV videos.
            fast_update (bool): Whether to stop at the first already-downloaded post.

        Returns:
            bool: True if the download is successful, False otherwise.
        """
        try:
            profile = Profile.from_username(self.loader.context, profile_name)
            self.loader.download_profile(
                profile,
                download_posts=download_posts,
                download_stories=download_stories,
                download_highlights=download_highlights,
                download_tagged=download_tagged,
                download_reels=download_reels,
                download_igtv=download_igtv,
                fast_update=fast_update,
            )
            return True
        except ProfileNotExistsException as e:
            print(f"Profile not found: {e}", file=sys.stderr)
            return False
        except InstaloaderException as e:
            print(f"Failed to download profile: {e}", file=sys.stderr)
            return False

    def download_hashtag(self, hashtag: str, max_count: Optional[int] = None) -> bool:
        """
        Download posts from a hashtag.

        Args:
            hashtag (str): Hashtag to download.
            max_count (Optional[int]): Maximum number of posts to download.

        Returns:
            bool: True if the download is successful, False otherwise.
        """
        try:
            self.loader.download_hashtag(hashtag=hashtag, max_count=max_count)
            return True
        except InstaloaderException as e:
            print(f"Failed to download hashtag: {e}", file=sys.stderr)
            return False

    def download_stories(self, profile_name: str) -> bool:
        """
        Download stories from a profile.

        Args:
            profile_name (str): Instagram profile name.

        Returns:
            bool: True if the download is successful, False otherwise.
        """
        try:
            profile = Profile.from_username(self.loader.context, profile_name)
            self.loader.download_stories([profile])
            return True
        except InstaloaderException as e:
            print(f"Failed to download stories: {e}", file=sys.stderr)
            return False

    def close(self):
        """Close the Instagram loader and clean up resources."""
        self.loader.close()