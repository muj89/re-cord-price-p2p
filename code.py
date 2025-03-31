import requests
import json
import pandas as pd
from datetime import datetime
import time

# إعداد الرابط والبيانات المطلوبة من Binance
url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"

# إعداد payload لطلب بيانات البيع والشراء (أول 30 عرض)
payload_sell = {
    "asset": "USDT",
    "fiat": "SDG",
    "tradeType": "SELL",
    "page": 1,
    "rows": 30
}

payload_buy = {
    "asset": "USDT",
    "fiat": "SDG",
    "tradeType": "BUY",
    "page": 1,
    "rows": 30
}

# دالة لجلب البيانات من Binance
def fetch_data(payload):
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"❌ فشل في جلب البيانات. حالة الاستجابة: {response.status_code}")
        return []

# دالة لإضافة البيانات إلى ملف Excel بدون مسح القديم
def append_to_excel(records):
    try:
        df_existing = pd.read_excel("binance_p2p_prices_buy_sell.xlsx")
        df_new = pd.DataFrame(records)
        df_updated = pd.concat([df_existing, df_new], ignore_index=True)
        df_updated.to_excel("binance_p2p_prices_buy_sell.xlsx", index=False)
    except FileNotFoundError:
        df = pd.DataFrame(records)
        df.to_excel("binance_p2p_prices_buy_sell.xlsx", index=False)

# تكرار العملية كل 5 ثوانٍ
while True:
    # جلب بيانات البيع والشراء
    sell_data = fetch_data(payload_sell)
    buy_data = fetch_data(payload_buy)

    # تحضير قائمة لتخزين البيانات
    records = []

    # إضافة بيانات البيع إلى القائمة مع تطبيق الشروط
    for item in sell_data:
        adv = item.get("adv", {})
        advertiser = item.get("advertiser", {})

        min_qty = adv.get("minSingleTransAmount")
        max_qty = adv.get("maxSingleTransAmount")
        is_merchant = advertiser.get("isMerchant", False)
        tradable_qty = float(adv.get("tradableQuantity", 0))

        if is_merchant or tradable_qty > 1000:
            record = {
                "وقت الطلب": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "سعر": adv.get("price"),
                "الكمية": adv.get("tradableQuantity"),
                "النوع": adv.get("tradeType"),
                "اسم المعلن": advertiser.get("nickName"),
                "وسيلة الدفع": adv.get("tradeMethods")[0].get("tradeMethodName") if adv.get("tradeMethods") else None,
                "هل هو تاجر": "نعم" if is_merchant else "لا",
                "الحد الأدنى للكمية": min_qty,
                "الحد الأقصى للكمية": max_qty
            }
            records.append(record)

    # إضافة بيانات الشراء إلى القائمة مع تطبيق الشروط
    for item in buy_data:
        adv = item.get("adv", {})
        advertiser = item.get("advertiser", {})

        min_qty = adv.get("minSingleTransAmount")
        max_qty = adv.get("maxSingleTransAmount")
        is_merchant = advertiser.get("isMerchant", False)
        tradable_qty = float(adv.get("tradableQuantity", 0))

        if is_merchant or tradable_qty > 1000:
            record = {
                "وقت الطلب": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "سعر": adv.get("price"),
                "الكمية": adv.get("tradableQuantity"),
                "النوع": adv.get("tradeType"),
                "اسم المعلن": advertiser.get("nickName"),
                "وسيلة الدفع": adv.get("tradeMethods")[0].get("tradeMethodName") if adv.get("tradeMethods") else None,
                "هل هو تاجر": "نعم" if is_merchant else "لا",
                "الحد الأدنى للكمية": min_qty,
                "الحد الأقصى للكمية": max_qty
            }
            records.append(record)

    # إضافة البيانات إلى ملف Excel
    if records:
        append_to_excel(records)
        print(f"\n✅ تم تحديث الأسعار وإضافتها في {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    else:
        print("\n❌ لم يتم العثور على أي بيانات تلبي الشروط.\n")

    # الانتظار لمدة 5 ثوانٍ قبل التحديث التالي
    time.sleep(5)
