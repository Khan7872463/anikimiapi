from requests_html import HTMLSession
from bs4 import BeautifulSoup
import requests
from anikimiapi.data_classes import *
from anikimiapi.error_handlers import *
import re
import lxml.html.clean as clean


class AniKimi:
    """
    A class to retrieve anime details and episode links from an anime website.
    """

    def __init__(self, gogoanime_token: str, auth_token: str):
        """
        Initializes the AniKimi class with the given tokens.
        
        Args:
            gogoanime_token (str): Token for Gogoanime.
            auth_token (str): Authorization token.
        """
        self.gogoanime_token = gogoanime_token
        self.auth_token = auth_token
        self.host = "https://gogoanime.ai"

    def search_anime(self, query: str) -> list:
        """
        Searches for anime based on the provided query string.
        
        Args:
            query (str): The search query string.
        
        Returns:
            list: A list of ResultObject instances with search results.
        
        Raises:
            NoSearchResultsError: If no search results are found.
            NetworkError: If there's a network connection error.
        """
        try:
            url1 = f"{self.host}/search.html?keyword={query}"
            session = HTMLSession()
            response = session.get(url1)
            response_html = response.text

            # Clean the HTML content
            cleaner = clean.Cleaner()
            cleaned_html = cleaner.clean_html(response_html)

            soup = BeautifulSoup(cleaned_html, 'html.parser')
            animes = soup.find("ul", {"class": "items"}).find_all("li")
            res_list_search = []
            for anime in animes:
                tit = anime.a["title"]
                urll = anime.a["href"]
                r = urll.split('/')
                res_list_search.append(ResultObject(title=f"{tit}", animeid=f"{r[2]}"))
            if not res_list_search:
                raise NoSearchResultsError("No Search Results found for the query")
            else:
                return res_list_search
        except requests.exceptions.ConnectionError:
            raise NetworkError("Unable to connect to the Server, Check your connection")

    def get_details(self, animeid: str) -> MediaInfoObject:
        """
        Retrieves the basic details of an anime using its anime ID.
        
        Args:
            animeid (str): The ID of the anime.
        
        Returns:
            MediaInfoObject: An object containing anime details.
        
        Raises:
            InvalidAnimeIdError: If the anime ID is invalid.
            NetworkError: If there's a network connection error.
        """
        try:
            animelink = f'{self.host}/category/{animeid}'
            response = requests.get(animelink)
            plainText = response.text

            # Clean the HTML content
            cleaner = clean.Cleaner()
            cleaned_html = cleaner.clean_html(plainText)

            soup = BeautifulSoup(cleaned_html, "lxml")
            source_url = soup.find("div", {"class": "anime_info_body_bg"}).img
            imgg = source_url.get('src')
            tit_url = soup.find("div", {"class": "anime_info_body_bg"}).h1.string
            lis = soup.find_all('p', {"class": "type"})
            plot_sum = lis[1]
            pl = plot_sum.get_text().split(':')
            pl.remove(pl[0])
            sum = ""
            plot_summary = sum.join(pl)
            type_of_show = lis[0].a['title']
            ai = lis[2].find_all('a')
            genres = [link.get('title') for link in ai]
            year1 = lis[3].get_text()
            year2 = year1.split(" ")
            year = year2[1]
            status = lis[4].a.get_text()
            oth_names = lis[5].get_text()
            lnk = soup.find(id="episode_page")
            ep_str = str(lnk.contents[-2])
            a_tag = ep_str.split("\n")[-2]
            a_tag_sliced = a_tag[:-4].split(">")
            last_ep_range = a_tag_sliced[-1]
            y = last_ep_range.split("-")
            ep_num = y[-1]
            res_detail_search = MediaInfoObject(
                title=f"{tit_url}",
                year=int(year),
                other_names=f"{oth_names}",
                season=f"{type_of_show}",
                status=f"{status}",
                genres=genres,
                episodes=int(ep_num),
                image_url=f"{imgg}",
                summary=f"{plot_summary}"
            )
            return res_detail_search
        except AttributeError:
            raise InvalidAnimeIdError("Invalid animeid given")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Unable to connect to the Server, Check your connection")

    def get_episode_link_advanced(self, animeid: str, episode_num: int) -> MediaLinksObject:
        """
        Retrieves streamable and downloadable links for a given anime ID and episode number.
        
        Args:
            animeid (str): The ID of the anime.
            episode_num (int): The episode number.
        
        Returns:
            MediaLinksObject: An object containing various media links.
        
        Raises:
            InvalidAnimeIdError: If the anime ID or episode number is invalid.
            NetworkError: If there's a network connection error.
            InvalidTokenError: If the provided tokens are invalid.
        """
        try:
            ep_num_link_get = episode_num
            str_qry_final = animeid
            animelink = f'{self.host}/category/{str_qry_final}'
            response = requests.get(animelink)
            plainText = response.text

            # Clean the HTML content
            cleaner = clean.Cleaner()
            cleaned_html = cleaner.clean_html(plainText)

            soup = BeautifulSoup(cleaned_html, "lxml")
            lnk = soup.find(id="episode_page")
            source_url = lnk.find("li").a
            anime_title = soup.find("div", {"class": "anime_info_body_bg"}).h1.string
            ep_num_tot = source_url.get("ep_end")
            last_ep = int(ep_num_tot)
            episode_url = '{}{}-episode-{}'
            url = episode_url.format(self.host, str_qry_final, ep_num_link_get)
            master_keyboard_list = []
            cookies = {
                'gogoanime': self.gogoanime_token,
                'auth': self.auth_token
            }
            response = requests.get(url=url, cookies=cookies)
            plaintext = response.text

            # Clean the HTML content
            cleaned_html = cleaner.clean_html(plaintext)

            soup = BeautifulSoup(cleaned_html, "lxml")
            download_div = soup.find("div", {'class': 'cf-download'}).findAll('a')
            links_final = MediaLinksObject()
            for links in download_div:
                download_links = links['href']
                q_name_raw = links.text.strip()
                q_name_raw_list = q_name_raw.split('x')
                quality_name = q_name_raw_list[1]
                if quality_name == "360":
                    links_final.link_360p = download_links
                elif quality_name == "480":
                    links_final.link_480p = download_links
                elif quality_name == "720":
                    links_final.link_720p = download_links
                elif quality_name == "1080":
                    links_final.link_1080p = download_links
            anime_multi_link_initial = soup.find('div', {'class': 'anime_muti_link'}).findAll('li')
            anime_multi_link_initial.remove(anime_multi_link_initial[0])
            chumma_list = []
            for l in anime_multi_link_initial:
                get_a = l.find('a')
                video_links = get_a['data-video']
                valid = video_links[0:4]
                if valid == "http":
                    pass
                else:
                    video_links = f"https:{video_links}"
                chumma_list.append(video_links)
            anime_multi_link_initial.remove(anime_multi_link_initial[0])
            for other_links in anime_multi_link_initial:
                get_a_other = other_links.find('a')
                downlink = get_a_other['data-video']
                quality_name = other_links.text.strip().split('C')[0]
                if quality_name == "Streamsb":
                    links_final.link_streamsb = downlink
                elif quality_name == "Xstreamcdn":
                    links_final.link_xstreamcdn = downlink
                elif quality_name == "Streamtape":
                    links_final.link_streamtape = downlink
                elif quality_name == "Mixdrop":
                    links_final.link_mixdrop = downlink
                elif quality_name == "Mp4Upload":
                    links_final.link_mp4upload = downlink
                elif quality_name == "Doodstream":
                    links_final.link_doodstream = downlink
            res = requests.get(chumma_list[0])
            plain = res.text

            # Clean the HTML content
            cleaned_html = cleaner.clean_html(plain)

            s = BeautifulSoup(cleaned_html, "lxml")
            t = s.findAll('script')
            hdp_js = t[2].string
            hdp_link_initial = re.search("(?P<url>https?://[^\s]+)", hdp_js).group()
            links_final.link_360p = hdp_link_initial
            return links_final
        except AttributeError:
            raise InvalidAnimeIdError("Invalid animeid or episode_num given")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Unable to connect to the Server, Check your connection")
        except TypeError:
            raise InvalidTokenError("Invalid tokens passed, Check your tokens")            

def get_by_genres(self, genre_name: str, limit: int = 60) -> list:
        """
        Get anime by genres, The genre object has the following genres working,

        action, adventure, cars, comedy, dementia, demons, drama, dub, ecchi, fantasy,
        game, harem, hentai - Temporarily Unavailable, historical, horror, josei, kids,
        magic, martial-arts, mecha, military, music, mystery, parody, police, psychological,
        romance, samurai, school, sci-fi, seinen, shoujo, shoujo-ai, shounen-ai, shounen,
        slice-of-life, space, sports, super-power, supernatural, thriller, vampire,
        yaoi, yuri.

        Parameters:
            genre_name(``str``):
                The name of the genre. You should use any from the above mentioned genres.

            limit(``int``):
                The limit for the number of anime you want from the results. defaults to 60 (i.e, 3 pages)

        Returns:
            List of :obj:`-anikimiapi.data_classes.ResultObject`: On Success, the list of genre results is returned.
        """
        gen_ani = []

        def page_anime_scraper(soup_object) -> list:
            animes = soup_object.find("ul", {"class": "items"}).find_all("li")
            ani_results = []
            for anime in animes:
                tit = anime.a["title"]
                urll = anime.a["href"]
                r = urll.split('/')
                ani_results.append(ResultObject(title=f"{tit}", animeid=f"{r[2]}"))
            return ani_results

        def pagination_helper(current_page_source: str, url: str, limit: int) -> None:
            """A recursive helper function which helps to successively scrape anime from following pages
               (if there are any) till limit is reached. """
            soup = BeautifulSoup(current_page_source, "lxml")
            next_page = soup.find("li", {"class": "selected"}).findNext('li')

            if next_page is not None:
                try:
                    next_page_value = next_page.a.get('data-page')
                    next_page_url = f'{url}{next_page_value}'
                    next_page_src = requests.get(next_page_url).text

                    # Clean the HTML content
                    cleaner = clean.Cleaner()
                    cleaned_html = cleaner.clean_html(next_page_src)

                    soup = BeautifulSoup(cleaned_html, "lxml")

                    # Next/subsequent page results
                    next_page_results = page_anime_scraper(soup)
                    for anime in next_page_results:
                        if len(gen_ani) < limit:
                            gen_ani.append(anime)
                        else:
                            break
                    if len(gen_ani) < limit:
                        pagination_helper(next_page_src, url, limit)
                except AttributeError:
                    pass

        try:
            url = f"{self.host}/genre/{genre_name}?page="
            response = requests.get(url)
            plainText = response.text

            # Clean the HTML content
            cleaner = clean.Cleaner()
            cleaned_html = cleaner.clean_html(plainText)

            soup = BeautifulSoup(cleaned_html, "lxml")

            # Starting page
            starting_page_results = page_anime_scraper(soup)
            for anime in starting_page_results:
                if len(gen_ani) < limit:
                    gen_ani.append(anime)
                else:
                    break

            if len(gen_ani) < limit:
                pagination_helper(current_page_source=plainText, url=url, limit=limit)

            return gen_ani

        except (AttributeError, KeyError):
            raise InvalidGenreNameError("Invalid genre_name or page_num")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Unable to connect to server")

def get_airing_anime(self, count=10) -> list:
    """
    Get the currently airing anime and their animeid.

    Parameters:
        count(``int`` | ``str``, *optional*):
            The number of search results to be returned, Defaults to 10.

    Returns:
        List of :obj:`-anikimiapi.data_classes.ResultObject`: On Success, the list of currently airing anime results is returned.
    """
    try:
        if int(count) > 20:
            raise CountError("count parameter cannot exceed 20")
        else:
            url = f"{self.host}"
            response = requests.get(url)
            response_html = response.text

            # Clean the HTML content
            cleaner = clean.Cleaner()
            cleaned_html = cleaner.clean_html(response_html)

            soup = BeautifulSoup(cleaned_html, 'lxml')
            anime = soup.find("nav", {"class": "menu_series cron"}).find("ul")
            air = []
            for link in anime.find_all('a'):
                airing_link = link.get('href')
                name = link.get('title')  # name of the anime
                link_parts = airing_link.split('/')
                lnk_final = link_parts[2]  # animeid of anime
                air.append(ResultObject(title=f"{name}", animeid=f"{lnk_final}"))
            return air[:int(count)]
    except (IndexError, AttributeError, TypeError):
        raise AiringIndexError("No content found on the given page number")
    except requests.exceptions.ConnectionError:
        raise NetworkError("Unable to connect to server")
