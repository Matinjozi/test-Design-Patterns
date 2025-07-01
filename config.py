import asyncio
import json
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel


class BaseServiceModel(BaseModel):
    provider: str
    service_key: str
    category: Optional[str] = None
    price: float
    is_discounted: bool
    discount_text: Optional[str] = None


class RideAdapter(ABC):
    @abstractmethod
    async def adapt(self, response_json: str) -> List[BaseServiceModel]:
        """هر اداپتور باید لیستی از BaseServiceModel برگرداند"""
        ...


class TapsiPriceAdapter(RideAdapter):
    async def adapt(self, response_json: str) -> List[BaseServiceModel]:
        data = json.loads(response_json)
        out: List[BaseServiceModel] = []

        for cat in data.get("data", {}).get("categories", []):
            category_title = cat.get("title")
            for item in cat.get("items", []):
                srv = item.get("service", {})
                srv_key = srv.get("key")
                for p in srv.get("prices", []):
                    out.append(BaseServiceModel(
                        provider="tapsi",
                        service_key=srv_key,
                        category=category_title,
                        price=p.get("passengerShare"),
                        is_discounted=False,
                        discount_text=""
                    ))

        # حذف موارد تکراری با price و نگه‌داشتن فقط ۳ تای آخر
        unique_prices = {item.price: item for item in out}
        return list(unique_prices.values())[-3:]


class SnappAdapter(RideAdapter):
    async def adapt(self, response_json: str) -> List[BaseServiceModel]:
        data = json.loads(response_json)
        out: List[BaseServiceModel] = []

        for p in data.get("data", {}).get("prices", []):
            out.append(BaseServiceModel(
                provider="snapp",
                service_key=p.get("type"),
                category=None,
                price=p.get("final"),
                is_discounted=p.get("is_discounted_price"),
                discount_text=p.get("texts", {}).get("discounted_price", "")
            ))

        return out


# ----------- تست سریع -----------

async def demo():
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
    }'''  # paste actual string here
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
    }'''  # paste actual string here

    tapsi_adapter = TapsiPriceAdapter()
    snapp_adapter = SnappAdapter()

    tapsi_res = await tapsi_adapter.adapt(tapsi_raw)
    snapp_res = await snapp_adapter.adapt(snapp_raw)

    unified: List[BaseServiceModel] = tapsi_res + snapp_res
    for item in unified:
        print(json.dumps(item.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(demo())
