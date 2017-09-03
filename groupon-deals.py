#Author: Pavani Boga ( pavanianapala@gmail.com )
#Date : 09/03/2017
# Job : https://www.upwork.com/jobs/~01c15e3bc888b97c83
# This scraper gets all the groupon deals in a city
# Run : scrapy crawl groupon-deals -a city=san-jose -t csv -o san-jose.csv --logfile=san-jose.log
# -*- coding: utf-8 -*-
import scrapy
import re
from datetime import datetime

class DealItem(scrapy.Item):
    MerchantName = scrapy.Field()
    MerchantOffer = scrapy.Field()
    CouponPrice = scrapy.Field()
    CouponsBrought = scrapy.Field()
    CouponsToday = scrapy.Field()
    OfferEnd = scrapy.Field()


class DealsSpider(scrapy.Spider):
    name = 'deals'
    allowed_domains = ['www.groupon.com']
    base_url = 'http://www.groupon.com'

    def __init__(self,city,*args,**kwargs):
        super(DealsSpider,self).__init__(*args,**kwargs)
        self.start_urls = ['http://www.groupon.com/browse/%s' %city]

    def coupons_today(self,response):
        today_selector = response.xpath('//*[@id="purchase-cluster"]/div/div[4]/div[2]/div[2]/text()').extract_first()
        if today_selector and 'bought' in today_selector:
            re_today = re.search(r'(.*) bought today',today_selector.strip())
            return re_today.group(1)
        else:
            return 'NA'


    def parse(self, response):
        for deal in response.xpath('//*[@id="pull-cards"]/figure/a/@href').extract():
            yield scrapy.Request(deal,callback=self.parse_deal)

        next_url = response.xpath('//*[@rel="next"]/@href').extract_first()
        if next_url:
            yield scrapy.Request(self.base_url+next_url,callback=self.parse)


    def parse_deal(self,response):
        item = DealItem()


        #check if merchant has multiple offers or not and parse accordingly
        if response.xpath('//li[contains(@data-bhd,"titleLength")]'):
            for offer in response.xpath('//li[contains(@data-bhd,"titleLength")]'):
                #this is for avoiding duplicates without coupon prices
                if offer.xpath('.//*[@name="option"]/@data-formatted-price').extract_first():
                    item['MerchantName'] = response.xpath('//span[@class="merchant-info"]/span/text()').extract_first()
                    item['MerchantOffer'] = offer.xpath('.//h3/text()').extract_first()
                    item['CouponPrice'] = offer.xpath('.//*[@name="option"]/@data-formatted-price').extract_first()
                    item['CouponsBrought'] = re.search(r'Over\s(.*)\sbought',offer.xpath('.//*[@name="option"]/@data-sold-message').extract_first()).group(1) + '+' if offer.xpath('.//*[@name="option"]/@data-sold-message').extract_first() else 'NA'
                    item['CouponsToday'] = self.coupons_today(response)
                    item['OfferEnd'] = re.search(r'"endAt":"(.*)"',response.xpath('//*[@data-bhw="BuyButton"]/@data-bhd').extract_first()).group(1)
                    yield item
        # Handling Hotels
        elif response.xpath('//*[@data-category-id="gateways"]'):
            item['MerchantName'] = response.xpath('//*[@id="purchase-cluster"]/aside/h5/text()').extract_first()
            item['MerchantOffer'] = response.xpath('//*[@id="deal-title"]/text()').extract_first().strip()
            item['CouponPrice'] = response.xpath('//*[@itemprop="lowprice"]/@content').extract_first()
            item['CouponsBrought'] = re.search(r'Over\s(.*)\sbought', response.xpath('//*[@class="qty-bought icon-group"]/text()').extract_first()).group(1) + '+' if re.search(r'Over\s(.*)\sbought',response.xpath('//*[@class="qty-bought icon-group"]/text()').extract_first()) else 'NA'
            item['CouponsToday'] = self.coupons_today(response)
            date_str = re.search(r'"endAt":(.*?)}', response.xpath('//*[@id="global-container"]/div[2]/script[2]/text()').extract_first()).group(1)
            if date_str:
                item['OfferEnd'] = datetime.fromtimestamp(int(date_str[:-3])).strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                item['OfferEnd'] = 'NA'

            yield item
        # Handling cashback claims
        elif response.xpath('//*[contains(@data-bhd,"cloClaim")]'):
            item['MerchantName'] = response.xpath('//*[@class="merchant-info"]/span/text()').extract_first()
            item['MerchantOffer'] = response.xpath('//*[@id="deal-title"]/text()').extract_first().strip()
            item['CouponPrice'] = 'NA'
            item['CouponsBrought'] = re.search(r'Over\s(.*)\sclaimed', response.xpath('//*[@class="sold-message details"]/text()').extract_first().strip()).group(1) if re.search(r'Over\s(.*)\sclaimed',response.xpath('//*[@class="sold-message details"]/text()').extract_first().strip()) else 'NA'
            item['CouponsToday'] = self.coupons_today(response)
            item['OfferEnd'] = re.search(r'"endAt":"(.*)"', response.xpath('//*[@data-bhw="BuyButton"]/@data-bhd').extract_first()).group(1)
            yield item

        #Handling single cases
        elif response.xpath('//*[@id="buy-link"]'):
            item['MerchantName'] = response.xpath('//*[@class="merchant-info"]/span/text()').extract_first() if response.xpath('//*[@class="merchant-info"]/span/text()') else 'NA'
            item['MerchantOffer'] = response.xpath('//*[@id="deal-title"]/text()').extract_first().strip()
            item['CouponPrice'] = response.xpath('//*[@itemprop="lowprice"]/@content').extract_first()
            re_brought = response.xpath('//*[@class="qty-bought icon-group"]/text()').extract_first()
            if re_brought:
                item['CouponsBrought'] = re.search(r'Over\s(.*)\sbought',response.xpath('//*[@class="qty-bought icon-group"]/text()').extract_first()).group(1) + '+'
            else:
                item['CouponsBrought'] = 'NA'
            item['CouponsToday'] = self.coupons_today(response)
            item['OfferEnd'] = re.search(r'"endAt":"(.*?)"',response.xpath('//*[@data-bhw="BuyButton"]/@data-bhd').extract_first()).group(1)
            yield item
