import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, Any


class RideAdapter(ABC):
    @abstractmethod
    async def adapt(self, response_json: str) -> Dict[str, Any]:
        pass


class TapsiPriceAdapter(RideAdapter):
    async def adapt(self, response_json: str) -> Dict[str, Any]:
        data = json.loads(response_json)
        services_info = []

        categories = data.get('data', {}).get('categories', [])
        for category in categories:
            category_title = category.get('title')
            for item in category.get('items', []):
                service = item.get('service', {})
                service_key = service.get('key')
                for price in service.get('prices', []):
                    services_info.append({
                        'category': category_title,
                        'service': service_key,
                        'price': price.get('passengerShare')
                    })

        # حذف تکراری‌ها و نگه داشتن ۳ مورد آخر
        unique_services = self._remove_duplicates_keep_last_3(services_info)

        return {'services': unique_services}

    def _remove_duplicates_keep_last_3(self, services):
        """حذف تکراری‌ها بر اساس قیمت با حفظ ترتیب"""
        # ایجاد دیکشنری با قیمت به عنوان کلید
        price_to_service = {}
        for service in services:
            price_to_service[service['price']] = service

        # تبدیل به لیست و نگه داشتن ۳ مورد آخر
        unique_services = list(price_to_service.values())
        return unique_services[-3:]


# داده تست که از خودت گرفتم
tapsi_raw = '''{
  "result": "OK",
  "data": {
    "categories": [
      {
        "key": "SUGGESTION",
        "title": "پیشنهادی",
        "items": [
          {
            "service": {
              "key": "STANDARD",
              "prices": [{"type": "CERTAIN", "passengerShare": 65000}]
            }
          },
          {
            "service": {
              "key": "WAIT_AND_SAVE",
              "prices": [{"type": "CERTAIN", "passengerShare": 60000}]
            }
          },
          {
            "service": {
              "key": "PLUS",
              "prices": [{"type": "CERTAIN", "passengerShare": 85000}]
            }
          }
        ]
      },
      {
        "key": "NORMAL",
        "title": "دربستی",
        "items": [
          {
            "service": {
              "key": "STANDARD",
              "prices": [{"type": "CERTAIN", "passengerShare": 65000}]
            }
          },
          {
            "service": {
              "key": "PLUS",
              "prices": [{"type": "CERTAIN", "passengerShare": 85000}]
            }
          }
        ]
      },
      {
        "key": "ECONOMIC",
        "title": "اقتصادی",
        "items": [
          {
            "service": {
              "key": "WAIT_AND_SAVE",
              "prices": [{"type": "CERTAIN", "passengerShare": 60000}]
            }
          }
        ]
      }
    ]
  }
}'''


class SnappAdapter(RideAdapter):
    async def adapt(self, response_json: str) -> Dict[str, Any]:
        data = json.loads(response_json)
        services_info = []

        prices = data.get('data', {}).get('prices', [])
        for price_info in prices:
            service_type = price_info.get('type')
            final_price = price_info.get('final')
            is_discounted = price_info.get('is_discounted_price')
            discounted_text = price_info.get('texts', {}).get('discounted_price', '')
            services_info.append({
                'type': service_type,
                'final_price': final_price,
                'is_discounted': is_discounted,
                'discounted_text': discounted_text
            })

        return {'services': services_info}


snapp_raw = '''{
    "status": 200,
    "data": {
        "prices": [
            {
                "final": 840000,
                "final_lower": null,
                "is_hurry_enable": true,
                "raw_fare": null,
                "raw_fare_lower": null,
                "type": "1",
                "is_free_ride": false,
                "is_discounted_price": false,
                "is_surged": false,
                "is_enabled": true,
                "is_post_price": false,
                "tag": "",
                "texts": {
                    "free_ride": "",
                    "free_ride_footer": "",
                    "discounted_price": "تخفیف برای شما!",
                    "discounted_price_footer": "تبریک، این سفر ۰٪ تخفیف دارد. از سفرتان لذت ببرید!",
                    "surge": "",
                    "surge_footer": "",
                    "disabled_reason": "",
                    "surge_link": null,
                    "promotion_message": "",
                    "promotion_message_footer": "",
                    "discount_and_surge_price": "تخفیف برای افزایش قیمت موقت",
                    "discount_and_surge_price_footer": "به دلیل بالا رفتن تقاضا، هزینه این سفر به طور موقت از سقف شورای شهر برای تاکسی تلفنی بیشتر است. همچنین این سرویس شامل ۰٪ تخفیف شده است.",
                    "post_price": "",
                    "post_price_footer": "",
                    "priority_offer_button": "درخواست پیشتاز"
                },
                "distance": 0,
                "eta": "",
                "eta_texts": [
                    "16:09"
                ],
                "items": [],
                "promotion_error": "",
                "voucher_type": 0,
                "tcv": "",
                "pickup_eta": "",
                "flexi": {
                    "is_enabled": false,
                    "config": {
                        "open_dialogue_button": "",
                        "title": "",
                        "description": "",
                        "confirm_button": "",
                        "warning_message": ""
                    },
                    "prices": null
                }
            },
            {
                "final": 1000000,
                "final_lower": null,
                "is_hurry_enable": true,
                "raw_fare": 1110000,
                "raw_fare_lower": null,
                "type": "2",
                "is_free_ride": false,
                "is_discounted_price": true,
                "is_surged": false,
                "is_enabled": true,
                "is_post_price": false,
                "tag": "",
                "texts": {
                    "free_ride": "",
                    "free_ride_footer": "",
                    "discounted_price": "تخفیف برای شما!",
                    "discounted_price_footer": "تبریک، این سفر ۹٪ تخفیف دارد. از سفرتان لذت ببرید!",
                    "surge": "",
                    "surge_footer": "",
                    "disabled_reason": "",
                    "surge_link": null,
                    "promotion_message": "",
                    "promotion_message_footer": "",
                    "discount_and_surge_price": "تخفیف برای افزایش قیمت موقت",
                    "discount_and_surge_price_footer": "به دلیل بالا رفتن تقاضا، هزینه این سفر به طور موقت از سقف شورای شهر برای تاکسی تلفنی بیشتر است. همچنین این سرویس شامل ۹٪ تخفیف شده است.",
                    "post_price": "",
                    "post_price_footer": "",
                    "priority_offer_button": "درخواست پیشتاز"
                },
                "distance": 0,
                "eta": "",
                "eta_texts": [
                    "16:09"
                ],
                "items": [],
                "promotion_error": "",
                "voucher_type": 0,
                "tcv": "",
                "pickup_eta": "",
                "flexi": {
                    "is_enabled": false,
                    "config": {
                        "open_dialogue_button": "",
                        "title": "",
                        "description": "",
                        "confirm_button": "",
                        "warning_message": ""
                    },
                    "prices": null
                }
            }
        ],
        "tag": "0",
        "confirm_before_ride": false,
        "confirm_before_ride_message": "",
        "waiting": [
            {
                "key": "0m-5m",
                "price": 30000,
                "text": "۰ تا ۵ دقیقه"
            },
            {
                "key": "5m-10m",
                "price": 60000,
                "text": "۵ تا ۱۰ دقیقه"
            },
            {
                "key": "10m-15m",
                "price": 90000,
                "text": "۱۰ تا ۱۵ دقیقه"
            },
            {
                "key": "15m-20m",
                "price": 120000,
                "text": "۱۵ تا ۲۰ دقیقه"
            },
            {
                "key": "20m-25m",
                "price": 150000,
                "text": "۲۰ تا ۲۵ دقیقه"
            },
            {
                "key": "25m-30m",
                "price": 180000,
                "text": "۲۵ تا ۳۰ دقیقه"
            },
            {
                "key": "30m-45m",
                "price": 270000,
                "text": "۳۰ تا ۴۵ دقیقه"
            },
            {
                "key": "45m-1h",
                "price": 360000,
                "text": "۴۵ دقیقه تا ۱ ساعت"
            },
            {
                "key": "1h-1h30m",
                "price": 540000,
                "text": "۱ تا ۱.۵ ساعت"
            },
            {
                "key": "1h30m-2h",
                "price": 720000,
                "text": "۱.۵ تا ۲ ساعت"
            },
            {
                "key": "2h-2h30m",
                "price": 900000,
                "text": "۲ تا ۲.۵ ساعت"
            },
            {
                "key": "2h30m-3h",
                "price": 1080000,
                "text": "۲.۵ تا ۳ ساعت"
            },
            {
                "key": "3h-3h30m",
                "price": 1260000,
                "text": "۳ تا ۳.۵ ساعت"
            },
            {
                "key": "3h30m-4h",
                "price": 1440000,
                "text": "۳.۵ تا ۴ ساعت"
            },
            {
                "key": "0m-5m",
                "price": 30000,
                "text": "۰ تا ۵ دقیقه"
            },
            {
                "key": "5m-10m",
                "price": 60000,
                "text": "۵ تا ۱۰ دقیقه"
            },
            {
                "key": "10m-15m",
                "price": 90000,
                "text": "۱۰ تا ۱۵ دقیقه"
            },
            {
                "key": "15m-20m",
                "price": 120000,
                "text": "۱۵ تا ۲۰ دقیقه"
            },
            {
                "key": "20m-25m",
                "price": 150000,
                "text": "۲۰ تا ۲۵ دقیقه"
            },
            {
                "key": "25m-30m",
                "price": 180000,
                "text": "۲۵ تا ۳۰ دقیقه"
            },
            {
                "key": "30m-45m",
                "price": 270000,
                "text": "۳۰ تا ۴۵ دقیقه"
            },
            {
                "key": "45m-1h",
                "price": 360000,
                "text": "۴۵ دقیقه تا ۱ ساعت"
            },
            {
                "key": "1h-1h30m",
                "price": 540000,
                "text": "۱ تا ۱.۵ ساعت"
            },
            {
                "key": "1h30m-2h",
                "price": 720000,
                "text": "۱.۵ تا ۲ ساعت"
            },
            {
                "key": "2h-2h30m",
                "price": 900000,
                "text": "۲ تا ۲.۵ ساعت"
            },
            {
                "key": "2h30m-3h",
                "price": 1080000,
                "text": "۲.۵ تا ۳ ساعت"
            },
            {
                "key": "3h-3h30m",
                "price": 1260000,
                "text": "۳ تا ۳.۵ ساعت"
            },
            {
                "key": "3h30m-4h",
                "price": 1440000,
                "text": "۳.۵ تا ۴ ساعت"
            }
        ],
        "details": null
    }
}'''


async def main():
    tapsi_adapter = TapsiPriceAdapter()
    snapp_adapter = SnappAdapter()

    # تست آداپتور تپسی
    tapsi_result = await tapsi_adapter.adapt(tapsi_raw)
    print("🚗 Tapsi Services (Last 3 Unique Prices):")
    for service in tapsi_result['services']:
        print(f"  {service['category']} - {service['service']}: {service['price']:,} تومان")

    print("\n" + "=" * 50 + "\n")

    # تست آداپتور اسنپ
    snapp_result = await snapp_adapter.adapt(snapp_raw)
    print("🚕 Snapp Services:")
    for service in snapp_result['services']:
        discount_status = "✅ دارد" if service['is_discounted'] else "❌ ندارد"
        print(f"  نوع {service['type']}: {service['final_price']:,} تومان - تخفیف: {discount_status}")

asyncio.run(main())