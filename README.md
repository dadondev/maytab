# Maytab 📅

Maytab — bu **aiogram 3** asosida qurilgan Telegram bot bo'lib, maktab dars jadvallarini boshqarish uchun mo'ljallangan. Bot foydalanuvchilarga o'z sinf jadvallarini ko'rish, avtomatik yuborish xizmatidan foydalanish, adminlarga esa jadvallarni yuklash va guruhlarga rejali yuborish imkonini beradi.

---

## ✨ Asosiy imkoniyatlar

### 👤 Foydalanuvchi uchun
- **Ro'yxatdan o'tish** — ism, telefon raqami va sozlamalar orqali avtomatik registratsiya.
- **Mening jadvallarim** — o'z sinf jadvallarini tanlash va boshqarish (qo'shish / o'chirish).
- **Umumiy jadval** — barcha sinflar jadvallarini ko'rish.
- **Kunlik jadval** — jadvalni bosganda hafta kunlari (Dushanba...Shanba) tugmalari chiqadi, tanlangan kun ko'rsatiladi.
- **Sozlamalar** — avtomatik yuborish va SMS xizmatini yoqish/o'chirish.
- **Avtomatik yuborish** — har kuni 08:00 da foydalanuvchiga bugungi jadval yuboriladi.

### 🛡️ Qo'riqchi (Guard) uchun
- `/guard` buyrug'i bilan qo'riqchi paneli ochiladi.
- **Ertangi jadval** — ertangi kun jadvallari dars soni bo'yicha guruhlanadi (masalan, "5 soat dars borlar: 1-A, 1-B...").
- **Sinf jadvalni ko'rish** — sinf va guruh tanlab to'liq jadvalni ko'rish.

### 👮‍♀️ Admin uchun
- `/admin` buyrug'i bilan admin paneli ochiladi.
- **📥 Jadvalni yuklash** — Excel (.xlsx) faylni yuklab, ma'lumotlar bazasiga joylash yoki vazifa yaratish.
- **📋 Vazifalar** — vazifalarni ko'rish, yakunlash va o'chirish.
- **📬 Xabar yuborish** — barcha foydalanuvchilarga xabar (broadcast) yuborish.
- **🛡️ Qo'riqchilar** — qo'riqchilarni qo'shish va olib tashlash (chat ID orqali).
- **Yashirin buyruq** — parol orqali adminlarni boshqarish.

### 👥 Guruh chat imkoniyati
- Bot guruhga qo'shilganda avtomatik sinf tanlash so'rovini yuboradi.
- Guruhga biriktirilgan sinf jadvali har kuni **05:00** da (bugungi) va **16:00** da (ertangi) yuboriladi.

### ⏰ Vazifalar (Task) tizimi
- Vazifa yaratishda sana va vaqt belgilanadi.
- Belgilangan vaqt kelganda jadval avtomatik bazaga yuklanadi.
- Vazifa davomida adminalarga start, muvaffaqiyat yoki xato xabari yuboriladi.
- Vazifa yakunlangach barcha foydalanuvchilarga jadval yangilangani haqida xabar va yangi jadval yuboriladi.

---

## 🛠 Texnologiyalar

| Texnologiya | Maqsad |
|---|---|
| **aiogram 3** | Telegram Bot API bilan ishlash |
| **SQLAlchemy 2** | Ma'lumotlar bazasi (ORM) |
| **SQLite** | Ma'lumotlar bazasi |
| **openpyxl** | Excel fayllarni o'qish |
| **phonenumbers** | Telefon raqamni tekshirish |
| **python-dotenv** | Muhit o'zgaruvchilarini yuklash |

---

## 📁 Loyiha tuzilishi

```
maytab/
├── main.py                  # Botni ishga tushirish (polling + scheduler)
├── pyproject.toml           # Loyiha va bog'liqliklar
├── requirements.txt         # Bog'liqliklar ro'yxati
├── .env                     # Muhit o'zgaruvchilari (TOKEN, DB_URL, ADMIN_PASSWORD)
│
├── bot/
│   ├── bot.py               # Asosiy router va start handler
│   ├── admin.py             # Admin router (upload, xabar, vazifalar, qo'riqchilar)
│   ├── guard.py             # Qo'riqchi panellari
│   ├── group_chat.py        # Guruhga qo'shilish va sinf biriktirish
│   └── bootstrap.py         # Bot instansiyasi (aylanma importlarni oldini oladi)
│
├── config/
│   ├── utils.py             # TOKEN, DB_URL, ADMIN_PASSWORD va regexlar
│   └── valid_phone.py       # Telefon raqamni tekshirish
│
├── db/
│   ├── engine.py            # SQLAlchemy engine
│   ├── schemas.py           # Modelalar (User, Role, Task, Grade, Group, GroupChat)
│   └── queries.py           # Ma'lumotlar bazasi funksiyalari
│
├── excel/
│   └── get_data_from_file.py  # Excel jadvalni o'qish va qayta ishlash
│
├── files/
│   ├── file.py              # Faylni yuklab olish
│   └── downloads/           # Yuklab olingan fayllar (vaqtinchalik)
│
├── keyboards/
│   ├── menu.py              # Asosiy menyu
│   ├── my_tables.py         # Mening jadvallarim
│   ├── user_tables.py       # Sinf/guruh tanlash tugmalari
│   ├── settings.py          # Sozlamalar
│   ├── register.py          # Registratsiya tugmalari
│   ├── admin_menu.py        # Admin menyu
│   ├── admin_tasks.py       # Vazifalar tugmalari
│   ├── admin_security.py    # Qo'riqchilar tugmalari
│   ├── admin_broadcast.py   # Xabar yuborish tugmalari
│   ├── guard_menu.py        # Qo'riqchi panel tugmalari
│   └── group_chat.py        # Guruh sinf tanlash tugmalari
│
├── middlewares/
│   ├── existUserMiddleware.py   # Foydalanuvchi mavjudligini tekshirish
│   ├── isAdminMiddleware.py     # Admin rolini tekshirish
│   └── isGuardMiddleware.py     # Qo'riqchi rolini tekshirish
│
├── services/
│   └── scheduler.py         # Rejalashtirilgan yuborishlar (05:00, 08:00, 16:00)
│
└── states/
    ├── register_state.py    # Registratsiya holatlari
    └── setting_state.py     # Sozlama holatlari
```

---

## 🚀 O'rnatish va ishga tushirish

### 1. Muhit o'zgaruvchilari
`.env` faylini yarating va quyidagilarni kiriting:

```env
TOKEN=YOUR_BOT_TOKEN
DB_URL="sqlite:///database.db"
ADMIN_PASSWORD="secret_admin_password"
```

- **`TOKEN`** — Telegram'dan bot token (BotFather orqali).
- **`DB_URL`** — ma'lumotlar bazasi manzili.
- **`ADMIN_PASSWORD`** — `/admin` yashirin buyrug'i uchun parol.

### 2. Bog'liqliklarni o'rnatish

```bash
pip install -r requirements.txt
# yoki
uv sync
```

### 3. Botni ishga tushirish

```bash
python main.py
```

Bot ishga tushganda avtomatik:
- Ma'lumotlar bazasi tablitsalarini (`init_db`) yaratadi.
- `/start` va boshqa buyruqlarni qabul qiladi.
- Scheduler (rejalashtirilgan yuborishlar) ishlay boshlaydi.

---

## 🔑 Buyruqlar

| Buyruq | Tavsif | Kim uchun |
|---|---|---|
| `/start` | Bot bilan ishlashni boshlash | Barcha |
| `/admin` | Admin paneli | Admin |
| `/admin create <chat_id> <password>` | Foydalanuvchini admin qilish | — (parol orqali) |
| `/admin list <password>` | Adminlar ro'yxati | — (parol orqali) |
| `/admin remove <chat_id> <password>` | Admin ro'lidan olish | — (parol orqali) |
| `/guard` | Qo'riqchi paneli | Qo'riqchi |

---

## 📚 Ma'lumotlar bazasi modellari

| Model | Tavsif |
|---|---|
| `User` | Foydalanuvchi (ism, telefon, sozlamalar, tanlangan jadvallar) |
| `Role` | Rol (user / admin / guard) |
| `Task` | Vazifa (sana, fayl yo'li, holat: pending/running/completed/failed) |
| `Grade` | Sinf darajasi (1-11) |
| `Group` | Guruh/sinf jadvali |
| `GroupChat` | Telegram guruhi ↔ sinf biriktirish |

---

## ⏰ Rejalashtirilgan yuborishlar

| Vaqt | Nima yuboriladi |
|---|---|
| **05:00** | Bugungi jadval → biriktirilgan guruh chatlariga |
| **08:00** | Bugungi jadval → avtomatik yuborish yoqilgan foydalanuvchilarga |
| **16:00** | Ertangi jadval → biriktirilgan guruh chatlariga |

Vazifalar (task) vazifasi kelganda ham avtomatik bajariladi: jadval bazaga yuklanadi, barcha foydalanuvchilarga yangi jadval yuboriladi.

---

## 📝 Eslatmalar

- **Excel fayl formati**: Faqat `.xlsx` / `.xls` fayllar qabul qilinadi. Faylda ko'p varoq bo'lishi mumkin — barcha varoqlardan jadvallar yig'iladi.
- **Sinf ID formati**: `1-A`, `10-B` kabi (raqam-harf).
- **Xavfsizlik**: `/admin` yashirin buyrug'ini faqat `ADMIN_PASSWORD` ni bilganlar ishlata oladi. Tokenni ham, parolni ham ommaga oshkor qilmang.

---

## ❓ Muammolar

Agar bot ishlanmasa:
1. `.env` faylida `TOKEN` va `ADMIN_PASSWORD` to'g'ri kiritilganligini tekshiring.
2. Bir vaqtda faqat **bitta** bot instansiyasi ishlayotganiga ishonch hosil qiling (aks holda `TelegramConflictError` chiqadi).
3. `python main.py` bilan ishga tushirib, konsol xatosini tekshiring.
