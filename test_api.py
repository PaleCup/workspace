import unittest
from fastapi.testclient import TestClient
from main import app
from app.database import init_db

class TestFoodOrderSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_01_merchant_info(self):
        """测试商家信息获取与更新"""
        res = self.client.get("/api/merchant")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("name", data)
        self.assertIn("avg_rating", data)
        self.assertIn("gallery", data)
        self.assertTrue(len(data["gallery"]) > 0)

        # 切换营业状态
        toggle_res = self.client.post("/api/merchant/toggle-open")
        self.assertEqual(toggle_res.status_code, 200)
        new_status = toggle_res.json()["is_open"]
        # 恢复状态
        toggle_back = self.client.post("/api/merchant/toggle-open")
        self.assertEqual(toggle_back.json()["is_open"], 1 if new_status == 0 else 0)

    def test_02_dishes_and_categories(self):
        """测试分类和菜品接口"""
        cat_res = self.client.get("/api/categories")
        self.assertEqual(cat_res.status_code, 200)
        cats = cat_res.json()
        self.assertGreater(len(cats), 0)

        dish_res = self.client.get("/api/dishes")
        self.assertEqual(dish_res.status_code, 200)
        dishes = dish_res.json()
        self.assertGreater(len(dishes), 0)

        # 关键词搜索
        search_res = self.client.get("/api/dishes?keyword=虾")
        self.assertEqual(search_res.status_code, 200)
        search_dishes = search_res.json()
        self.assertTrue(any("虾" in d["name"] for d in search_dishes))

    def test_03_order_flow(self):
        """测试堂食与外卖点餐、金额计算与状态流转"""
        # 获取第一道菜品
        dishes = self.client.get("/api/dishes").json()
        dish1 = dishes[0]
        dish2 = dishes[1]

        # 提交新订单 (堂食)
        order_payload = {
            "dining_type": "dine_in",
            "table_number": "A08",
            "customer_name": "自动化测试员",
            "customer_phone": "13900000000",
            "remark": "少放辣，多用餐巾纸",
            "payment_method": "wechat",
            "items": [
                {"dish_id": dish1["id"], "quantity": 2},
                {"dish_id": dish2["id"], "quantity": 1}
            ]
        }
        create_res = self.client.post("/api/orders", json=order_payload)
        self.assertEqual(create_res.status_code, 200)
        order_data = create_res.json()
        order_id = order_data["order_id"]
        expected_total = round(dish1["price"] * 2 + dish2["price"] * 1, 2)
        self.assertEqual(order_data["total_amount"], expected_total)

        # 查看订单详情
        detail_res = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(len(detail["items"]), 2)
        self.assertEqual(detail["status"], "pending")

        # 状态推进: 待接单 -> 制作中 -> 待取餐 -> 已完成
        s1 = self.client.patch(f"/api/orders/{order_id}/status", json={"status": "preparing"})
        self.assertEqual(s1.status_code, 200)

        s2 = self.client.patch(f"/api/orders/{order_id}/status", json={"status": "delivering"})
        self.assertEqual(s2.status_code, 200)

        s3 = self.client.patch(f"/api/orders/{order_id}/status", json={"status": "completed"})
        self.assertEqual(s3.status_code, 200)
        self.assertEqual(s3.json()["status"], "completed")

    def test_04_review_and_reply_flow(self):
        """测试评价发表、统计指标计算以及商家回复"""
        rev_payload = {
            "customer_name": "资深食客",
            "rating": 5,
            "taste_rating": 5,
            "service_rating": 5,
            "content": "菜品口感很棒，汤非常浓郁，上菜速度也快！",
            "recommended_dishes": "宫保大虾球,金牌脆皮乳鸽",
            "tags": "分量足,食材新鲜",
            "dining_type": "堂食"
        }
        add_rev = self.client.post("/api/reviews", json=rev_payload)
        self.assertEqual(add_rev.status_code, 200)
        rev_id = add_rev.json()["id"]

        # 获取统计指标
        stats_res = self.client.get("/api/reviews/stats")
        self.assertEqual(stats_res.status_code, 200)
        stats = stats_res.json()
        self.assertGreaterEqual(stats["total_count"], 1)
        self.assertIn("stars", stats)

        # 商家回复此评价
        reply_res = self.client.post(f"/api/reviews/{rev_id}/reply", json={"reply": "非常感谢您的认可与赞美！欢迎下次光临！"})
        self.assertEqual(reply_res.status_code, 200)

        # 验证评价中包含回复
        reviews_list = self.client.get("/api/reviews?filter_type=with_reply").json()
        replied_review = next((r for r in reviews_list if r["id"] == rev_id), None)
        self.assertIsNotNone(replied_review)
        self.assertIn("非常感谢您的认可", replied_review["merchant_reply"])

    def test_05_admin_dashboard(self):
        """测试管理端数据看板"""
        res = self.client.get("/api/stats/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("today_orders", data)
        self.assertIn("today_revenue", data)
        self.assertIn("top_dishes", data)

if __name__ == "__main__":
    unittest.main()
