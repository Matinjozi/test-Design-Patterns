import jq
import json
from baseclass_adaptor import RideAdapter
from config import Settings
import asyncpg
import asyncio

settings = Settings()


async def get_connection(settings):
    return await asyncpg.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password)


class TapsiAdapter(RideAdapter):
    def __init__(self, settings):
        self.settings = settings

    async def adapt(self, response_json):
        conn = await get_connection(self.settings)
        try:
            data = json.loads(response_json)

            prices = jq.compile('.data.categories[].items[].service.prices[].passengerShare').input(data).all()

            unique_prices = list(set(prices))
            unique_prices.sort()

            if len(unique_prices) >= 3:
                price_economic = unique_prices[0]
                price_ordinary = unique_prices[1]
                price_plus = unique_prices[2]

                await conn.execute(
                    "INSERT INTO price_tapsi (price_service_ordinary, price_service_economic, price_service_plus) VALUES ($1, $2, $3)",
                    price_ordinary, price_economic, price_plus)

                return {"ordinary": price_ordinary, "economic": price_economic, "plus": price_plus}
            else:
                raise ValueError(f"تعداد قیمت‌های یافت شده کافی نیست: {len(unique_prices)}")

        finally:
            await conn.close()







class SnappAdapter(RideAdapter):
    def __init__(self, settings):
        self.settings = settings

    async def adapt(self, response_json):
        conn = await get_connection(self.settings)
        try:
            data = json.loads(response_json)

            regular_price = None
            plus_price = None

            price_options = data.get("data", {}).get("prices", [])

            for service in price_options:
                service_type = service.get("type")
                if service_type == "1":
                    regular_price = service.get("final")
                elif service_type == "2":
                    plus_price = service.get("final")

            if regular_price is not None and plus_price is not None:
                await conn.execute(
                    "INSERT INTO snapp_prices (regular_price, plus_price) VALUES ($1, $2)",
                    regular_price,
                    plus_price
                )
                print(f"Inserted into DB: Regular Price = {regular_price}, Plus Price = {plus_price}")
            else:
                print("Could not find one or both prices in the response.")

            return {
                "regular_price": regular_price,
                "plus_price": plus_price
            }

        except json.JSONDecodeError:
            print("Error decoding JSON response.")
            return None
        except Exception as e:

            print(f"An error occurred: {e}")
            return None
        finally:

            await conn.close()


async def get_clean_data(platform, response_json, settings: Settings):
    adapters = {
        "tapsi": TapsiAdapter(settings),
        "snapp": SnappAdapter(settings)
    }
    adapter = adapters.get(platform)
    if adapter:
        return await adapter.adapt(response_json)  # await اضافه شد
    else:
        raise ValueError("پلتفرم پشتیبانی نمی‌شود")


# Test data
tapsi_raw = '''{
 "result": "OK",
 "data": {
  "token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJwcmV2aWV3RGF0YSI6eyJvcmlnaW4iOnsibGF0aXR1ZGUiOjM0LjU3MTMxNDgsImxvbmdpdHVkZSI6NTAuODA4NjY5N30sImRlc3RpbmF0aW9ucyI6W3sibGF0aXR1ZGUiOjM0LjYzMjY2NTcsImxvbmdpdHVkZSI6NTAuODY2NDgyfV0sImhhc1JldHVybiI6ZmFsc2UsIndhaXRpbmdUaW1lIjowfSwicHJpY2VEYXRhIjpbeyJzZXJ2aWNlS2V5IjoiUExVUyIsIm51bWJlck9mUGFzc2VuZ2VycyI6MSwicGFzc2VuZ2VyU2hhcmUiOjg1MDAwfSx7InNlcnZpY2VLZXkiOiJXQUlUX0FORF9TQVZFIiwibnVtYmVyT2ZQYXNzZW5nZXJzIjoxLCJwYXNzZW5nZXJTaGFyZSI6NjAwMDB9LHsic2VydmljZUtleSI6IlNUQU5EQVJEIiwibnVtYmVyT2ZQYXNzZW5nZXJzIjoxLCJwYXNzZW5nZXJTaGFyZSI6NjUwMDB9LHsic2VydmljZUtleSI6IkRFTElWRVJZIiwibnVtYmVyT2ZQYXNzZW5nZXJzIjoxLCJwYXNzZW5nZXJTaGFyZSI6NzUwMDB9LHsic2VydmljZUtleSI6IkJJS0VfREVMSVZFUlkiLCJudW1iZXJPZlBhc3NlbmdlcnMiOjEsInBhc3NlbmdlclNoYXJlIjo1ODAwMH1dLCJ1dWlkIjoiNWU1MjYxNDAtMjgyYS0xMWYwLWEyMzktNzdlOTZkZDk1YWE3IiwiaWF0IjoxNzQ2MjgyMjg4LCJleHAiOjE3NDYyODIzNTgsImF1ZCI6ImRvcm9zaGtlOmFwcCIsImlzcyI6ImRvcm9zaGtlOnNlcnZlciIsInN1YiI6ImRvcm9zaGtlOnRva2VuIn0.wm0BYTBEPDhdpoOoVhWEeF-fyQDKGe8IPxWVRVx99Vkwgssv4zoG1ctfq4y4JnU-poVyAAkiwJITNLRq1Hkz0A",
  "ttl": 60,
  "surpriseElement": {
   "isApplied": false,
   "isEnabled": false,
   "rewardId": "0"
  },
  "hasReturn": false,
  "waitingTime": 0,
  "origin": {
   "location": {
    "latitude": 34.5713148,
    "longitude": 50.8086697
   },
   "province": "قم",
   "city": "قم",
   "address": "بلوار دانشگاه، نرسیده به میدان میدان علوم، پژوهشگاه حوزه و دانشگاه",
   "shortAddress": "بلوار دانشگاه، نرسیده به میدان میدان علوم، پژوهشگاه حوزه و دانشگاه"
  },
  "destinations": [
   {
    "location": {
     "latitude": 34.6326657,
     "longitude": 50.866482
    },
    "province": "قم",
    "city": "قم",
    "address": "بلوار امین، بعد از رسالت، بوستان نجمه",
    "shortAddress": "بلوار امین، بعد از رسالت، بوستان نجمه"
   }
  ],
  "categories": [
   {
    "key": "SUGGESTION",
    "title": "پیشنهادی",
    "items": [
     {
      "service": {
       "key": "STANDARD",
       "isAvailable": true,
       "disclaimer": "زمان تقریبی رسیدن شما به مقصد ۱۸:۲۰ است. امکان تغییر این زمان در شرایط خاص وجود دارد.",
       "subtitle": "پایان سفر: ۱۸:۲۰",
       "prices": [
        {
         "type": "CERTAIN",
         "numberOfPassengers": 1,
         "passengerShare": 65000,
         "discount": 0
        }
       ],
       "pickupSuggestions": [],
       "isAuthenticationRequired": false
      }
     },
     {
      "service": {
       "key": "WAIT_AND_SAVE",
       "isAvailable": true,
       "disclaimer": "زمان تقریبی رسیدن شما به مقصد متناسب با زمان یافتن سفیر ممکن است تغییر نماید.",
       "subtitle": "تا ۱۰ دقیقه صبر کنید",
       "prices": [
        {
         "type": "CERTAIN",
         "numberOfPassengers": 1,
         "passengerShare": 60000,
         "discount": 0
        }
       ],
       "pickupSuggestions": [],
       "isAuthenticationRequired": false
      }
     },
     {
      "service": {
       "key": "PLUS",
       "isAvailable": true,
       "disclaimer": "زمان تقریبی رسیدن شما به مقصد ۱۸:۲۰ است. امکان تغییر این زمان در شرایط خاص وجود دارد.",
       "subtitle": "پایان سفر: ۱۸:۲۰",
       "prices": [
        {
         "type": "CERTAIN",
         "numberOfPassengers": 1,
         "passengerShare": 85000,
         "discount": 0
        }
       ],
       "pickupSuggestions": [],
       "isAuthenticationRequired": false,
       "notAvailableText": ""
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
       "isAvailable": true,
       "disclaimer": "زمان تقریبی رسیدن شما به مقصد ۱۸:۲۰ است. امکان تغییر این زمان در شرایط خاص وجود دارد.",
       "subtitle": "پایان سفر: ۱۸:۲۰",
       "prices": [
        {
         "type": "CERTAIN",
         "numberOfPassengers": 1,
         "passengerShare": 65000,
         "discount": 0
        }
       ],
       "pickupSuggestions": [],
       "isAuthenticationRequired": false
      }
     },
     {
      "service": {
       "key": "PLUS",
       "isAvailable": true,
       "disclaimer": "زمان تقریبی رسیدن شما به مقصد ۱۸:۲۰ است. امکان تغییر این زمان در شرایط خاص وجود دارد.",
       "subtitle": "پایان سفر: ۱۸:۲۰",
       "prices": [
        {
         "type": "CERTAIN",
         "numberOfPassengers": 1,
         "passengerShare": 85000,
         "discount": 0
        }
       ],
       "pickupSuggestions": [],
       "isAuthenticationRequired": false,
       "notAvailableText": ""
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
       "isAvailable": true,
       "disclaimer": "زمان تقریبی رسیدن شما به مقصد متناسب با زمان یافتن سفیر ممکن است تغییر نماید.",
       "subtitle": "تا ۱۰ دقیقه صبر کنید",
       "prices": [
        {
         "type": "CERTAIN",
         "numberOfPassengers": 1,
         "passengerShare": 60000,
         "discount": 0
        }
       ],
       "pickupSuggestions": [],
       "isAuthenticationRequired": false
      }
     }
    ]
   }
  ]
 }
}'''

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


async def main(settings):
    result = await get_clean_data("tapsi", tapsi_raw, settings)
    print("Tapsi Prices:", result)

    result = await get_clean_data("snapp", snapp_raw, settings)
    print("Snapp Prices:", result)


# اجرای اصلی برنامه
if __name__ == "__main__":
    asyncio.run(main(settings))