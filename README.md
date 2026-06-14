# 💎 AI-Powered Jewellery Shop Management System

A comprehensive, production-grade management system for jewellery shops featuring AI-powered recommendations, image recognition, sales prediction, and a full POS billing system.

## ✨ Features

### 🏪 Core Management
- **Dashboard** — Real-time KPIs, revenue charts, sales trends, low-stock alerts
- **Inventory Management** — CRUD for jewellery items with barcode generation and stock tracking
- **Customer Management** — Profiles with purchase history, loyalty points, birthdays, feedback
- **Sales & Billing** — GST invoice generation, PDF download, email, QR code, print support
- **Employee Management** — Attendance tracking, salary calculation, payslip PDF generation

### 🤖 AI Features
- **Recommendation Engine** — Content-based filtering using cosine similarity; recommends jewellery based on customer preferences and purchase history
- **Image Recognition** — Classifies jewellery type (ring, necklace, bracelet, earrings) from uploaded photos using OpenCV
- **Sales Prediction** — Random Forest ML model forecasting future sales with 90-day projections
- **Chatbot** — Natural language assistant for product inquiries, pricing, stock checks, and shop info

### 📊 Analytics
- Daily / Monthly / Yearly sales reports
- Category-wise revenue breakdown
- Profit & loss analysis
- Top-selling products
- Export to Excel (inventory, customers, bills, sales, attendance)

### 🌙 UI/UX
- Luxury gold/dark theme with **Light/Dark mode toggle** (persisted in localStorage)
- Premium font pairing: Playfair Display + Inter
- Glassmorphism cards, gold gradients, smooth animations
- Fully responsive (mobile, tablet, desktop)
- Real-time gold/silver price ticker

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3, Flask, Flask-Login |
| **Frontend** | Bootstrap 5, jQuery, DataTables, Chart.js |
| **Database** | SQLite (auto-seeded with demo data) |
| **AI/ML** | scikit-learn, OpenCV, NumPy, Pandas |
| **PDF** | ReportLab |
| **QR/Barcode** | qrcode, python-barcode |
| **Excel** | openpyxl, xlsxwriter |

## 🚀 Installation

### Prerequisites
- Python 3.10+
- pip (Python package manager)

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/KUSH648/AJSMS.git
   cd JewelHub
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

### Default Login Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Staff | `staff1` | `staff123` |

## 📸 Screenshots

<!-- Add screenshots here after deployment -->
*Screenshots coming soon.*

## 🌐 Live Demo

<!-- Add your deployed URL here -->
*Deployment URL placeholder — deploy to Render, Railway, or Vercel.*

## 📁 Project Structure

```
JewelHub/
├── ai/                    # AI/ML modules
│   ├── chatbot.py         # NLP chatbot
│   ├── image_recognition.py # OpenCV jewellery classifier
│   └── recommendation.py  # Content-based recommender
├── api/                   # Serverless entry point
├── database/
│   ├── db_setup.py        # Table creation + demo seeder
│   └── models.py          # Data access layer
├── ml_models/
│   ├── sales_prediction.py # Random Forest forecaster
│   └── train_model.py     # Training script
├── modules/
│   ├── auth.py            # Authentication & UserMixin
│   ├── billing.py         # GST calculation, invoice creation
│   ├── employees.py       # Salary & attendance logic
│   ├── inventory.py       # Item CRUD, barcode
│   └── sales.py           # Profit analysis
├── routes/                # Flask blueprints
├── static/
│   ├── css/style.css      # Complete design system (2743 lines)
│   ├── js/main.js         # All frontend logic
│   └── uploads/           # User uploads
├── templates/             # Jinja2 templates (31 pages)
├── utils/
│   └── pdf_generator.py   # ReportLab PDF invoice
├── app.py                 # Flask application factory
├── config.py              # Configuration
├── run.py                 # Entry point
└── requirements.txt       # Python dependencies
```

## 🔧 Configuration

Copy `env.example` to `.env` and configure:

```env
SECRET_KEY=your-secret-key
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
GOLD_API_KEY=your-goldapi-key
```

**Note:** The app works out of the box without any configuration — secrets have sensible defaults for development.

## 🚢 Deployment

### Deploy to Render
1. Push to GitHub
2. Create a new **Web Service** on Render
3. Set **Start Command**: `python run.py`
4. Set environment variables in Render dashboard

### Deploy to Vercel
1. The included `vercel.json` enables serverless deployment
2. Set `python run.py` as the build command

## 🔒 Security
- Password hashing with bcrypt
- Flask-Login session management with `remember me`
- Role-based access control (Admin / Staff)
- Soft-delete for inventory items and employees

## 📄 License

MIT License — see LICENSE file for details.

---

<p align="center">Made with 💎 for jewellery businesses worldwide</p>
