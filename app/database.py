import sqlite3
import os
import json
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "restaurant.db")

def get_db_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. 商家信息表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS merchant (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slogan TEXT,
        logo_url TEXT,
        banner_url TEXT,
        phone TEXT,
        address TEXT,
        opening_hours TEXT,
        is_open INTEGER DEFAULT 1,
        notice TEXT,
        story TEXT,
        avg_price REAL DEFAULT 45.0,
        tags TEXT,
        gallery TEXT
    )
    """)

    # 2. 菜品分类表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        icon TEXT
    )
    """)

    # 3. 菜品信息表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dishes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        original_price REAL,
        image_url TEXT,
        tags TEXT,
        monthly_sales INTEGER DEFAULT 0,
        rating REAL DEFAULT 5.0,
        is_available INTEGER DEFAULT 1,
        sort_order INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    """)

    # 4. 订单表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        dining_type TEXT NOT NULL, -- 'dine_in' or 'takeaway'
        table_number TEXT,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        delivery_address TEXT,
        remark TEXT,
        total_amount REAL NOT NULL,
        packaging_fee REAL DEFAULT 0.0,
        status TEXT DEFAULT 'pending', -- 'pending', 'preparing', 'delivering', 'completed', 'cancelled'
        payment_method TEXT DEFAULT 'wechat',
        payment_status TEXT DEFAULT 'paid',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 5. 订单明细表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT NOT NULL,
        dish_id INTEGER NOT NULL,
        dish_name TEXT NOT NULL,
        dish_price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id)
    )
    """)

    # 6. 评价表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        customer_name TEXT NOT NULL,
        avatar_url TEXT,
        rating INTEGER NOT NULL,
        taste_rating INTEGER NOT NULL DEFAULT 5,
        service_rating INTEGER NOT NULL DEFAULT 5,
        content TEXT NOT NULL,
        recommended_dishes TEXT,
        tags TEXT,
        dining_type TEXT DEFAULT '堂食',
        merchant_reply TEXT,
        replied_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    # 检查是否需要播种初始数据
    cursor.execute("SELECT COUNT(*) as count FROM merchant")
    if cursor.fetchone()["count"] == 0:
        seed_data(cursor)
        conn.commit()

    conn.close()

def seed_data(cursor):
    # 初始商家信息
    merchant_tags = json.dumps(["地道川粤风味", "二十年老店", "明厨亮灶", "精选有机食材", "免费WiFi", "免费停车"], ensure_ascii=False)
    gallery = json.dumps([
        "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1544025162-d76694265947?w=800&auto=format&fit=crop&q=80"
    ])
    story_text = """【拾味小馆】始创于2004年，专注于传统川味与经典粤菜的融合创新。二十年来，我们始终恪守“食不厌精，脍不厌细”的烹饪初心，坚持每天清晨直采新鲜时蔬与优质生鲜肉禽，拒绝使用预制调料包，用匠心火候唤醒食材本真风味。无论是朋友小酌、家庭聚餐还是商务宴请，拾味小馆都致力于为您呈现一段温润味蕾的美好时光。"""

    cursor.execute("""
    INSERT INTO merchant (
        name, slogan, logo_url, banner_url, phone, address, opening_hours, is_open, notice, story, avg_price, tags, gallery
    ) VALUES (
        '拾味小馆 · 匠心川粤菜',
        '地道烹饪二十载，寻回记忆中的烟火温度',
        'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=200&auto=format&fit=crop&q=80',
        'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1600&auto=format&fit=crop&q=80',
        '021-88886666 / 138-0000-8888',
        '上海市静安区南京西路1288号恒隆广场南座B1层-108号',
        '10:30 - 21:30 (全周无休)',
        1,
        '【秋季新品上市】秋风起，尝鲜正当时！本店新推出秘制鲍汁鲜鲍煲与滋补老鸭汤，堂食消费满168元即赠送招牌红糖冰粉一份！',
        ?,
        58.0,
        ?,
        ?
    )
    """, (story_text, merchant_tags, gallery))

    # 初始分类
    categories = [
        (1, "🔥 招牌推荐", 1, "flame"),
        (2, "🍲 经典热炒", 2, "utensils"),
        (3, "🍚 特色主食", 3, "bowl-rice"),
        (4, "🥣 养生滋补汤", 4, "soup"),
        (5, "🥗 精美凉菜", 5, "leaf"),
        (6, "🧋 沁爽饮品", 6, "coffee")
    ]
    cursor.executemany("INSERT INTO categories (id, name, sort_order, icon) VALUES (?, ?, ?, ?)", categories)

    # 初始菜品
    dishes = [
        # 招牌推荐
        (1, "宫保大虾球", "精选深海青虾仁，个大饱满，搭配香脆腰果与秘制糊辣荔枝汁，酸甜微麻过瘾", 68.0, 78.0,
         "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=600&auto=format&fit=crop&q=80",
         "招牌,酸甜微辣,人气TOP1", 420, 4.9, 1, 1),
        (1, "金牌脆皮乳鸽", "精选28天妙龄乳鸽，古法卤水浸煮后风干慢烤，外皮薄脆如纸，肉质鲜嫩多汁", 48.0, 56.0,
         "https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=600&auto=format&fit=crop&q=80",
         "必点,外脆里嫩", 380, 4.9, 1, 2),
        (1, "麻婆雪花和牛豆腐", "传统红油豆瓣结合细嫩雪花和牛肉粒，豆腐滑嫩烫口，花椒麻香浓郁", 52.0, 62.0,
         "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80",
         "下饭神器,中辣", 510, 4.8, 1, 3),

        # 经典热炒
        (2, "歌乐山辣子鸡", "选用林下散养三黄鸡斩小块炸至酥脆，配以贵州二荆条与四川汉源大红袍花椒爆炒", 45.0, 52.0,
         "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=600&auto=format&fit=crop&q=80",
         "香辣酥脆,经典川味", 360, 4.8, 1, 4),
        (2, "干炒特级牛河", "选用纯米现蒸河粉与鲜嫩牛里脊，猛火快炒镬气十足，牛肉爽滑豆芽清脆", 38.0, 42.0,
         "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=600&auto=format&fit=crop&q=80",
         "镬气满满,粤式经典", 490, 4.7, 1, 5),
        (2, "清炒高山有机芥蓝", "选用高山冷凉有机芥蓝，冰水浸泡后猪油猛火快烹，青翠碧绿，清甜无渣", 28.0, 32.0,
         "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80",
         "清淡爽口,时蔬", 290, 4.8, 1, 6),

        # 特色主食
        (3, "老上海葱油拌面", "现熬深色葱油酱汁，小葱熬至焦黄酥香，拌入劲道细面，每一口都齿颊留香", 18.0, 22.0,
         "https://images.unsplash.com/photo-1612927601601-6638404737ce?w=600&auto=format&fit=crop&q=80",
         "主食推荐,葱香浓郁", 620, 4.9, 1, 7),
        (3, "广式腊味煲仔饭", "精选丝苗米搭配皇上皇广味腊肠与陈年腊肉，瓦煲慢煲出金黄酥脆锅巴", 36.0, 42.0,
         "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&auto=format&fit=crop&q=80",
         "金黄脆锅巴,腊香扑鼻", 410, 4.9, 1, 8),
        (3, "鲜虾蟹籽烧卖皇 (4只)", "薄如蝉翼的黄色面皮包裹整颗鲜甜虾仁与上等猪肉馅，粒粒蟹籽点缀", 26.0, 30.0,
         "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=600&auto=format&fit=crop&q=80",
         "手工点心,料足味鲜", 340, 4.8, 1, 9),

        # 养生滋补汤
        (4, "花胶鲜鲍乌鸡煲 (盅)", "精选深海厚肉花胶与鲜鲍鱼，搭配三年乌鸡慢火细炖4小时，胶原满满，汤醇味浓", 46.0, 58.0,
         "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=600&auto=format&fit=crop&q=80",
         "养颜补气,醇厚鲜美", 220, 4.9, 1, 10),
        (4, "番茄浓汤酸菜鱼 (份)", "选用活水新鲜黑鱼切片，搭配老坛泡酸菜与有机熟成番茄熬制金汤，酸香开胃无刺", 62.0, 72.0,
         "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=600&auto=format&fit=crop&q=80",
         "酸甜微辣,鱼肉滑嫩", 380, 4.8, 1, 11),

        # 精美凉菜
        (5, "川香红油口水鸡", "皮脆肉滑的冷盘土鸡淋上现泼复合红油，麻辣鲜香、红亮诱人、开胃前菜首选", 35.0, 40.0,
         "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
         "开胃必点,红油香辣", 430, 4.8, 1, 12),
        (5, "芥末云耳伴秋葵", "脆爽黑云耳与鲜嫩秋葵，调制淡芥末青柠酱汁，爽口解腻清凉回甘", 22.0, 26.0,
         "https://images.unsplash.com/photo-1505576399279-565b52d4ac71?w=600&auto=format&fit=crop&q=80",
         "清爽开胃,低卡健康", 280, 4.7, 1, 13),

        # 沁爽饮品
        (6, "手作手打鸭屎香柠檬茶", "精选潮州凤凰单丛鸭屎香现萃茶汤，融入香水柠檬现捶爆汁，清香扑鼻微甜回甘", 16.0, 20.0,
         "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=600&auto=format&fit=crop&q=80",
         "现制冷饮,去油解腻", 780, 4.9, 1, 14),
        (6, "手工古法红糖冰粉", "传统手搓气泡冰粉，浇入自熬浓郁红糖浆，配以山楂碎、葡萄干与醪糟小圆子", 12.0, 15.0,
         "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=600&auto=format&fit=crop&q=80",
         "解辣神器,清凉爽滑", 650, 4.9, 1, 15)
    ]

    for dish in dishes:
        cursor.execute("""
        INSERT INTO dishes (
            category_id, name, description, price, original_price, image_url, tags, monthly_sales, rating, is_available, sort_order
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, dish)

    # 初始评价数据
    reviews = [
        (
            "ORD-20261025-0012",
            "林晨晨",
            "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80",
            5, 5, 5,
            "特别满意的一餐！和同事中午过来吃，宫保大虾球每个虾仁都特别大特别Q弹，荔枝糊辣味调得恰到好处。脆皮乳鸽名不虚传，皮超级脆，肉里汁水充沛。店内环境也很雅致，服务员小哥倒茶特别勤快，一定会再来！",
            "宫保大虾球,金牌脆皮乳鸽,手打鸭屎香柠檬茶",
            "分量足,食材新鲜,环境优雅,出餐快",
            "堂食",
            "感谢林女士的热情好评！宫保虾球与脆皮乳鸽一直是我们主厨团队的诚意之作，很高兴能合您的心意！我们新推出了秋季滋补靓汤，期待您和同事下次光临品尝！祝您生活愉快！",
            "2026-10-25 14:10:00",
            "2026-10-25 13:25:10"
        ),
        (
            "ORD-20261025-0008",
            "陈志远 (Alex)",
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80",
            5, 5, 5,
            "点了外卖送到公司，包装很讲究，汤汁一点都没撒出来，还有保温铝箔袋！干炒牛河镬气十足，牛肉很大片而且一点都不老。点名夸奖鸭屎香柠檬茶，冰度刚刚好，喝一口直接解腻。",
            "干炒特级牛河,手作手打鸭屎香柠檬茶",
            "包装精美,送达迅速,镬气十足,性价比高",
            "外卖",
            "感谢Alex先生对我们外卖出品与包装的肯定！外卖保温和锁鲜是我们一直严格把控的细节，能让您在办公室也吃上如堂食般热气腾腾的牛河是我们最大的欣慰！",
            "2026-10-25 12:55:00",
            "2026-10-25 12:30:45"
        ),
        (
            "ORD-20261024-0019",
            "苏晴天",
            "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100&auto=format&fit=crop&q=80",
            5, 5, 4,
            "周末家庭聚餐选在这里太明智了！爸妈对老鸭汤和腊味煲仔饭赞不绝口，锅巴金黄酥脆焦香，浇上特调酱油简直是绝配。红糖冰粉里的醪糟小圆子很地道，甜而不腻，推荐！",
            "广式腊味煲仔饭,手工古法红糖冰粉,花胶鲜鲍乌鸡煲",
            "家庭聚餐首选,菜品新鲜,味道地道",
            "堂食",
            "看到叔叔阿姨吃得开心，我们整个后厨都倍感振奋！煲仔饭现点现焗就是为了那一口酥脆锅巴，欢迎常带家人回家吃饭！",
            "2026-10-24 21:05:00",
            "2026-10-24 20:18:22"
        ),
        (
            "ORD-20261024-0005",
            "王建国",
            "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&auto=format&fit=crop&q=80",
            4, 4, 4,
            "辣子鸡炸得很透很香，就是对于我这种不太能吃辣的人稍微有点偏辣了，不过下酒真是一流！葱油拌面葱香很浓，面条很有筋道。整体性价比在静安区来说相当不错了。",
            "歌乐山辣子鸡,老上海葱油拌面",
            "分量足,性价比高",
            "堂食",
            "感谢王先生的客观评价与支持！我们的辣子鸡遵循地道川味，辣度确实比较足。下次您点餐时可以在备注里注明“微辣”，后厨会贴心为您减辣椒比例哦，期待您的再次惠顾！",
            "2026-10-24 15:30:00",
            "2026-10-24 14:02:15"
        ),
        (
            "ORD-20261023-0021",
            "喵呜爱吃鱼",
            "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop&q=80",
            5, 5, 5,
            "酸菜鱼太惊艳了！黑鱼片又薄又滑，完全没有刺，汤底酸辣开胃，我和闺蜜连汤都快喝完了。环境特别舒服，适合拍照打卡，灯光很柔和，音乐也很好听。",
            "番茄浓汤酸菜鱼,鲜虾蟹籽烧卖皇",
            "食材新鲜,拍照好看,环境舒适",
            "堂食",
            None,
            None,
            "2026-10-23 19:45:00"
        )
    ]

    for rev in reviews:
        cursor.execute("""
        INSERT INTO reviews (
            order_id, customer_name, avatar_url, rating, taste_rating, service_rating,
            content, recommended_dishes, tags, dining_type, merchant_reply, replied_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rev)

    # 初始示例订单
    sample_orders = [
        ("ORD-20261026-0001", "dine_in", "A08", "周铭轩", "13912345678", None, "免葱，少辣，请尽快出餐", 124.0, 0.0, "preparing", "wechat", "paid", "2026-10-26 09:30:00", "2026-10-26 09:32:00"),
        ("ORD-20261026-0002", "takeaway", None, "李雨欣", "13887654321", "恒隆广场办公楼18层 创想科技", "多放餐巾纸和餐具", 82.0, 3.0, "pending", "alipay", "paid", "2026-10-26 09:48:00", "2026-10-26 09:48:00"),
        ("ORD-20261025-0012", "dine_in", "B03", "林晨晨", "13700001111", None, "无特殊要求", 132.0, 0.0, "completed", "wechat", "paid", "2026-10-25 12:10:00", "2026-10-25 13:15:00")
    ]

    for o in sample_orders:
        cursor.execute("""
        INSERT INTO orders (
            id, dining_type, table_number, customer_name, customer_phone, delivery_address,
            remark, total_amount, packaging_fee, status, payment_method, payment_status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, o)

    # 订单明细
    order_items = [
        ("ORD-20261026-0001", 1, "宫保大虾球", 68.0, 1, 68.0),
        ("ORD-20261026-0001", 3, "麻婆雪花和牛豆腐", 52.0, 1, 52.0),
        ("ORD-20261026-0001", 6, "手作手打鸭屎香柠檬茶", 16.0, 2, 32.0),
        ("ORD-20261026-0002", 4, "干炒特级牛河", 38.0, 1, 38.0),
        ("ORD-20261026-0002", 9, "鲜虾蟹籽烧卖皇 (4只)", 26.0, 1, 26.0),
        ("ORD-20261026-0002", 14, "手作手打鸭屎香柠檬茶", 16.0, 1, 16.0),
        ("ORD-20261025-0012", 1, "宫保大虾球", 68.0, 1, 68.0),
        ("ORD-20261025-0012", 2, "金牌脆皮乳鸽", 48.0, 1, 48.0),
        ("ORD-20261025-0012", 14, "手作手打鸭屎香柠檬茶", 16.0, 1, 16.0)
    ]

    for item in order_items:
        cursor.execute("""
        INSERT INTO order_items (order_id, dish_id, dish_name, dish_price, quantity, subtotal)
        VALUES (?, ?, ?, ?, ?, ?)
        """, item)
