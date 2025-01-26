"""
This script defines a Scrapy spider named `SIBASpider` that crawls the Sukkur IBA University website to extract information about instructors from various departments. The extracted information includes the instructor's name, designation, email, biography, and education details.
Classes:
    SIBASpider(scrapy.Spider): A Scrapy spider to crawl and parse instructor information from the Sukkur IBA University website.
Functions:
    start_requests(self): Generates initial requests to the faculty pages of different departments.
    parse(self, response): Parses the main faculty page to extract links to individual instructor details pages.
    parse_instructor_details(self, response, name, designation): Parses the instructor details page to extract detailed information about the instructor.
    handle_error(self, failure): Handles errors that occur during the crawling process.
Global Variables:
    instructors_data (dict): A dictionary to store the extracted instructor information.
Usage:
    The script uses Scrapy's `CrawlerProcess` to start the crawling process and writes the extracted data to a JSON file named 'instructors_data.json'.
    """
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
        urls = [
            'https://iba-suk.edu.pk/faculty/management-science',
            'https://iba-suk.edu.pk/faculty/computer-science',
            'https://iba-suk.edu.pk/faculty/electrical-engineering',
            'https://iba-suk.edu.pk/faculty/Computer-system-engineering',
            'https://iba-suk.edu.pk/faculty/education',
            'https://iba-suk.edu.pk/faculty/mathematics',
            'https://iba-suk.edu.pk/faculty/supporting-faculty/english',
            'https://iba-suk.edu.pk/faculty/physical-education',
            'https://iba-suk.edu.pk/faculty/Media-Communication'
        ]
        
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        instructor_blocks = response.css('article.course-thumbnail > div.description')
        for instructor_block in instructor_blocks:
            instructor_name_top = instructor_block.css('a:nth-of-type(1)::text').extract_first()
            instructor_designation_top = instructor_block.css('a:nth-of-type(2)::text').extract_first()
            instructor_details_link = instructor_block.xpath('./div[2]/a/@href').extract_first()
            yield response.follow(url=instructor_details_link, callback=self.parse_instructor_details, cb_kwargs={'name': instructor_name_top, 'designation': instructor_designation_top}, errback=self.handle_error )
         

    def parse_instructor_details(self, response, name, designation):
         
        details_block = response.css('div#page-main div.inner')
        
        if not details_block:
            self.logger.warning("No details block found")
            instructors_data[name] = {
                'designation': designation,
                'email': "Not available",
                'biography': "Not available",
                'education': {},
            }
            return
        
        instructor_name = details_block.css('header>h2::text').extract_first()
        
        instructor_designation = details_block.xpath('./figure[1]/text()').extract_first()
        
        instructor_email_block = details_block.css('p.quote::text').extract_first()
        email_matches = re.findall(r'[a-zA-Z0-9._]+@iba-suk.edu.pk', instructor_email_block)
        instructor_email = email_matches[0] if email_matches else "Not available"
        
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
                
        except Exception:
            education = "Not available"

        instructors_data[instructor_name] = {
            'designation': instructor_designation,
            'email': instructor_email,
            'biography': instructor_biography.strip() if instructor_biography else "Not available",
            'education': education_dict
            
        }


    def handle_error(self, failure):
        self.logger.error(f"Request failed with error: {repr(failure)}")
        self.logger.error(f"Failed URL: {failure.request.url}")
        self.logger.error(f"Response status: {failure.value.response.status if failure.value.response else 'N/A'}")

process = CrawlerProcess()
process.crawl(SIBASpider)
process.start()

with open('instructors_data.json', 'w') as f:
    json.dump(instructors_data, f, indent=4)
        
    
    