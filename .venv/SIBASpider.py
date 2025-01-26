import scrapy
from scrapy.crawler import CrawlerProcess
import regex as re
import json

instructors_data = {}

class SIBASpider(scrapy.Spider):
    """
    This class is a spider that crawls the Sukkur IBA University website to get the instructors' information.
    """
    name = 'siba_instructors_spider'
    
    def start_requests(self):
        urls = ['https://iba-suk.edu.pk/faculty/management-science', 'https://iba-suk.edu.pk/faculty/computer-science', 'https://iba-suk.edu.pk/faculty/electrical-engineering', 'https://iba-suk.edu.pk/faculty/Computer-system-engineering', 'https://iba-suk.edu.pk/faculty/education', 'https://iba-suk.edu.pk/faculty/mathematics', 'https://iba-suk.edu.pk/faculty/supporting-faculty/english', 'https://iba-suk.edu.pk/faculty/physical-education', 'https://iba-suk.edu.pk/faculty/Media-Communication']
        
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        instructor_blocks = response.css('article.course-thumbnail > div.description')
        instructor_name_top = instructor_blocks.css('a:nth-of-type(1)::text').extract_first()
        instructor_designation_top = instructor_blocks.css('a:nth-of-type(2)::text').extract_first()
        for instructor_block in instructor_blocks:
            instructor_details_link = instructor_block.xpath('./div[2]/a/@href').extract_first()
            yield response.follow(url=instructor_details_link, callback=self.parse_instructor_details, cb_kwargs={'name': instructor_name_top, 'designation': instructor_designation_top}, errback=self.handle_error )
         

    def parse_instructor_details(self, response, name, designation):
         
        details_block = response.css('div#page-main div.inner')
        
        if not details_block:
            print("No details block found")
            instructors_data[name] = {
                'designation': designation,
                'email': "Not available",
                'biography': "Not available",
                'education': "Not available",
            }
            return
        
        instructor_name = details_block.css('header>h2::text').extract_first()
        instructor_designation = details_block.xpath('./figure[1]/text()').extract_first()
        instructor_email_block = details_block.css('p.quote::text').extract_first()
        instructor_email = re.findall(r'[a-zA-Z0-9._]+@iba-suk.edu.pk', instructor_email_block)[0]
        instructor_biography = details_block.css('p:nth-of-type(2)::text').extract_first()
        
        education_dict = {}

        try:
            education = ""

            education_table_block = details_block.css('div.table-responsive>table:nth-of-type(1)>tbody>tr')
            
            for idx, row in enumerate(education_table_block):
                education_entry = row.css('td::text').extract()
                education_dict[idx+1] = {
                    'degree': education_entry[0].strip(),
                    'institute': education_entry[1].strip(),
                    'major': education_entry[2].strip(),
                    'year': education_entry[3].strip()
                }
                
        except:
            education = "Not available"

        instructors_data[instructor_name] = {
            'designation': instructor_designation,
            'email': instructor_email,
            'biography': instructor_biography.strip(),
            'education': education_dict
            
        }


    def handle_error(self, failure):
        self.logger.error(repr(failure))

process = CrawlerProcess()
process.crawl(SIBASpider)
process.start()

with open('instructors_data.json', 'w') as f:
    json.dump(instructors_data, f, indent=4)
        
    
    