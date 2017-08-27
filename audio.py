# This scraper scrapes the www.bible.is site and get the audio info of 200+ preachings in 800+ languages
# -*- coding: utf-8 -*-
import scrapy
import re
from mutagen.mp3 import MP3
import urllib.request
import csv

class BibleItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    language = scrapy.Field()
    country = scrapy.Field()
    url = scrapy.Field()
    duration = scrapy.Field()


class AudioSpider(scrapy.Spider):
    name = "audio"
    allowed_domains = ["faithcomesbyhearing.com","bible.is"]
    start_urls = (
        'https://www.faithcomesbyhearing.com/audio-bibles/bible-recordings',
    )
    fields = ['Language','Country','URL','Duration']
    file = csv.writer(open('bible.csv','w'))
    file.writerow([fields])

    def parse(self, response):
        ng_init = response.xpath('/html/body/div[5]/div/div[1]/div/div[1]/@ng-init').extract()[0].strip()
        #ng_init = "{name:'Acateco', url:'http://www.bible.is/KNJSBI/Matt/1', country:'Guatemala'}"
        for line in ng_init.split('\n'):
            item = BibleItem()
            if  re.search(r'url:',line):
                item['country'] = re.search(r'country:\'(.*?)\'',line).group(1)
                item['language'] = re.search(r'name:\'(.*?)\'',line).group(1)
                item['url'] = re.search(r'url:\'(.*?)\'',line).group(1)
                item['duration'] = []
                yield scrapy.Request(item['url'],callback=self.parse_audio, meta={'item': item})

    def parse_audio(self,response):
        item = response.meta['item']
        audio_info = response.xpath('//*[@id="main-container"]/script[1]').extract()[0].strip()
        m = re.search(r'var audioUrl = "(.*?)"',audio_info)
        if m and m.group(1):
            audio_url = 'http:' + m.group(1)
            file,headers = urllib.request.urlretrieve(audio_url)
            audio = MP3(file)
            item['duration'].append(audio.info.length)
        else:
            item['duration'].append(' No Audio ') 
       
        # pagination
        next_page = response.xpath('//link[@rel="next"]/@href').extract()[0].strip() if response.xpath('//link[@rel="next"]/@href') else None
        if next_page:
            yield scrapy.Request(next_page,callback=self.parse_audio,meta={'item': item})
        else:
            self.file.writerow([item['language'],item['country'],item['url'],item['duration']])
       
