class LinkCrawler:
    def __init__(self, initial_url):
        self.initial_url = initial_url
        self.links = []
        self.visited_links = []
        self.session = AsyncHTMLSession()

    def crawl(self):
        self.crawl_link(self.initial_url)

    def crawl_link(self, initial_url):
        pass
