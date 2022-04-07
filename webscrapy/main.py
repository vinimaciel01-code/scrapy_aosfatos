import scrapy

status_list = ['contraditorio',
               'falso',
               'exagerado',
               'impreciso',
               'insustentavel',
               'verdadeiro']

class AosFatosSpider(scrapy.Spider):
    name = 'aos_fatos'
    start_urls = ['https://aosfatos.org/']

    def parse(self, response):
        links = response.xpath('//div[contains(@class, "drop-checamos")]//a/@href').getall()
        for link in links:
            yield scrapy.Request(
                response.urljoin(link),
                callback=self.parse_category
            )

    def parse_category(self, response):
        cards = response.css('a.entry-item-card::attr(href)').getall()
        for card in cards:
            yield scrapy.Request(
                response.urljoin(card),
                callback=self.parse_news
            )

        pages = response.css('.pagination a::attr(href)').getall()
        for page in pages:
            yield scrapy.Request(
                response.urljoin(page),
                callback=self.parse_category
            )

    def parse_news(self, response):
        title = response.css('article h1::text').get()
        date = ' '.join(response.css('div.publish-date::text').get().split())
        
        # tem dois tipos diferentes de paginas
        # 1. blockquote + status dentro do id da imagem
        # 2. blockquote//p + status dentro de figure//figcaption::text
        # https://www.aosfatos.org/noticias/veja-todas-falas-checadas-de-paes-e-crivella/

        quotes = response.xpath('//article//blockquote')
        # quote = quotes[0] 
        for quote in quotes:
           
            ## QUOTES ##

            # texto do blockquote
            quote_text = quote.css('::text').get()
            quote_text = quote_text.rstrip('\n').rstrip('\r')

            # texto dentro do <p> dentro do bloquote
            if quote_text == '':
                quote_text = quote.css('p::text').get()

            ## STATUS ##
            
            # escrita na dentro da classe @data-image-id da imagem
            status = quote.xpath('./preceding-sibling::p//img//@data-image-id').getall()
            if status:
                status = status[-1]
                status = status.replace('.png','')
                status = status.rstrip('\n').rstrip('\r')
                status = status.lower()

            # escrito em texto, dentro de <figure><figcaption>.
            if status not in status_list:
                status = quote.xpath('./preceding-sibling::figure//figcaption//text()').getall()
                if status:
                    status = status[-1]
                    status = status.lower()

            # escrito em texto, dentro de <figure><figcaption><outras tags>
            if status not in status_list:
                status = quote.xpath('./preceding-sibling::figure//figcaption//*[not(contains(text(), "\r\n"))]//text()').getall()
                if status:
                    status = status[-1]
                    status = status.lower()

            # escrito em texto, dentro do parágrafo anterior <p>
            if status not in status_list:
                status = quote.xpath('./preceding-sibling::p//text()').getall()
                if status:
                    status = status[-1]
                    status = status.lower()

            if status in status_list:
                yield {
                    'title': title,
                    'date': date,
                    'url': response.url,
                    'quote': quote_text,
                    'status': status   
                }
