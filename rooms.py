# This scrapes the student.com web site to check the room's availability for different countries and different cities
# -*- coding: utf-8 -*-
import scrapy
from lxml import etree
import re
import json

class RoomItem(scrapy.Item):
    country = scrapy.Field()
    city = scrapy.Field()
    property = scrapy.Field()
    address = scrapy.Field()
    first_description = scrapy.Field()
    second_description = scrapy.Field()
    features = scrapy.Field()
    no_beds = scrapy.Field()
    no_rooms = scrapy.Field()
    room_type = scrapy.Field()
    room_name = scrapy.Field()
    bathroom = scrapy.Field()
    availability = scrapy.Field()
    price = scrapy.Field()
    review = scrapy.Field()

class RoomsSpider(scrapy.Spider):
    name = "rooms"
    allowed_domains = ["student.com"]
    start_urls = (
        'https://www.student.com/en-gb/uk',
    )
    base_url = 'https://www.student.com'

    def parse(self, response):
        item = RoomItem()
        item['country'] = response.url.split('/')[-1]
        for city in response.xpath('//*[@id="top"]/main/section[1]/div/ul/li'):
            city_link = city.xpath('a/@href').extract()[0].strip()
            yield scrapy.Request(self.base_url+city_link,callback=self.parse_city,meta={'item': item, 'proxy' : "http://70.248.28.13:8080" })

    def parse_city(self, response):
       item = response.meta['item']
       item['city'] = response.url.split('/')[-1]
       for area in response.xpath('//*[@id="areas"]/div/ul/li'):
           area_link = area.xpath('a/@href').extract()[0].strip()
           yield scrapy.Request(self.base_url+area_link,callback=self.parse_area,meta={'item': item})

    def parse_area(self,response):
        item = response.meta['item']
        view_all = response.xpath('//*[@id="top"]/main/section[6]/div/a')
        # add accomodation to get all the listings
        if view_all:
            url_list = response.url.split('/')
            url_list = url_list[:-1] + ['accommodation',url_list[-1]]
            new_url = '/'.join(url_list)
            yield scrapy.Request(new_url,callback=self.parse_property_list,meta={'item': item})
        else:
            yield scrapy.Request(response.url,callback=self.parse_property_nolist,meta={'item': item})

    def parse_property_list(self,response):
        item = response.meta['item']
        for property in response.xpath('//*[@id="top"]/main/div/section/div[2]/div[2]/ol/li'):
            property_link = property.xpath('div/div/a/@href').extract()[0].strip()
            yield scrapy.Request(self.base_url + property_link,callback=self.parse_property,meta={'item': item})

    def parse_property_nolist(self,response):
        item = response.meta['item']
        for property in response.xpath('//*[@id="top"]/main/section[6]/div/ul/li'):
            property_link = property.xpath('a/@href').extract()[0].strip()
            yield scrapy.Request(self.base_url + property_url,callback=self.parse_property,meta={'item': item})

    def parse_property(self,response):
        item = response.meta['item']
        item['property'] = response.xpath('//h1[re:test(@class,"heading*")]/text()').extract()[0].strip()
        item['review'] = response.xpath('//*[@id="pr-snippet-310-1"]/div/div[1]/span/text()').extract()[0].strip() if  response.xpath('//*[@id="pr-snippet-310-1"]/div/div[1]/span/text()') else ''
        item['address'] = response.xpath('//*[@id="about"]/div[1]/text()').extract()[0].strip()
        item['first_description'] = " ".join([summary.xpath('text()').extract()[0].strip() for summary in response.xpath('//*[@id="property-summary"]/div/div/p')])
        item['second_description'] = " ".join([about.xpath('//*[count(child::*) = 0]/text()').extract()[0].rstrip() for about in response.xpath('//*[@id="about"]/div[2]/p')])
        item['features'] = " ".join([feature.xpath('text()').extract()[0].strip() for feature in response.xpath('//*[@id="facility"]/ul/li')])
        item['no_beds'] = response.xpath('//*[@id="top"]/main/div[1]/div/div[2]/ul/li[1]/text()').extract()[0].strip().split()[0]
        item['no_rooms'] = response.xpath('//*[@id="top"]/main/div[1]/div/div[2]/ul/li[2]/text()').extract()[0].strip().split()[0]

         # parsing rooms
        root = etree.HTML(response.text)
        rooms = json.loads(re.search(r'units:(.*)',root.findall('.//script')[8].text).group(1))
        for room in rooms:
            item['room_type'] = room['categoryName']
            item['room_name'] = room['name']
            item['bathroom'] = room['listings'][0]['bathroomType']
            item['availability'] = room['listings'][0]['availability']
            item['price'] = room['listings'][0]['price']
            yield item
    
         
        




