# 💚 SplitEase - Smart Expense Sharing Made Simple

A modern, full-stack expense sharing application that makes splitting bills with friends, roommates, and travel groups effortless. Built with FastAPI backend and Streamlit frontend, SplitEase provides real-time split calculations, smart settlement suggestions, and an intuitive user experience.

## 📌 Project Overview

**What is SplitEase?**

SplitEase is a Splitwise-inspired expense sharing platform that helps you track shared expenses and automatically calculates who owes what to whom. Perfect for:

- 🏠 **Roommates** - Split rent, utilities, groceries
- 👥 **Friend Groups** - Share restaurant bills, movie tickets
- ✈️ **Travel Groups** - Manage trip expenses, accommodations
- 🎉 **Events** - Split party costs, group activities

## 🚀 Key Features

### 💰 Expense Management

- ➕ **Add Expenses** - Quick expense entry with smart validation
- ✏️ **Edit & Delete** - Full CRUD operations with real-time preview
- 📜 **Expense History** - Filterable list with search by person, group, category

### 🔄 Flexible Split Methods

- **Equal Split** - Divide equally among participants
- **Percentage Split** - Custom percentage allocation with real-time validation
- **Exact Amount Split** - Specify exact amounts per person

### 🎯 Smart Features

- **Auto-populate People** - Reuse participants from previous expenses
- **Real-time Validation** - Instant feedback on split calculations
- **Dynamic Forms** - UI adapts based on selected split method
- **Settlement Optimization** - Minimize transactions with smart settlement suggestions

### 📊 Financial Insights

- **Balance Dashboard** - See who owes what at a glance
- **Settlement Suggestions** - Optimized payment recommendations
- **Expense Analytics** - Track spending by category and group

## 🖥️ Frontend (Streamlit)

The Streamlit frontend provides an intuitive, responsive interface with four main sections:

### 📱 Main Pages

- **➕ Add Expense** - Dynamic form with real-time split inputs
- **✏️ Edit/Delete** - Modify existing expenses with live preview
- **📜 Expense History** - Filterable expense list with advanced search
- **📊 Dashboard** - Balance overview and settlement recommendations

### 🎨 Dynamic UI Features

- **Smart Split Inputs** - Form fields appear instantly when split method changes
- **Real-time Validation** - Live feedback on percentage totals and exact amounts
- **Responsive Layout** - Optimized for desktop and mobile viewing
- **Dark Theme** - Modern dark UI with green accent colors

## 🧩 Backend (FastAPI)

Production-ready REST API with comprehensive validation and error handling.

### 🔗 API Endpoints

#### Expense Management

```http
GET    /api/v1/expenses           # Get all expenses
POST   /api/v1/expenses           # Create new expense
GET    /api/v1/expenses/{id}      # Get expense by ID
PUT    /api/v1/expenses/{id}      # Update expense
DELETE /api/v1/expenses/{id}      # Delete expense
```

#### Financial Operations

```http
GET    /api/v1/balances           # Get balance summary
GET    /api/v1/settlements        # Get settlement suggestions
GET    /api/v1/people             # Get all participants
```

#### System Health

```http
GET    /api/v1/health             # Database health check
GET    /docs                      # Interactive API documentation
```

### 📋 Sample API Requests

**Create Equal Split Expense:**

```json
{
  "amount": 120.0,
  "description": "Team lunch",
  "paid_by": "Alice",
  "participants": ["Alice", "Bob", "Charlie"],
  "split_type": "equal",
  "category": "Food"
}
```

**Create Percentage Split Expense:**

```json
{
  "amount": 200.0,
  "description": "Groceries",
  "paid_by": "Bob", 
  "participants": ["Alice", "Bob", "Charlie"],
  "split_type": "percentage",
  "shares": {
    "Alice": 40.0,
    "Bob": 40.0, 
    "Charlie": 20.0
  }
}
```

## 🗃️ Tech Stack

### Backend

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Async ORM with PostgreSQL
- **Pydantic** - Data validation and serialization
- **PostgreSQL** - Production database

### Frontend

- **Streamlit** - Interactive web app framework
- **Pandas** - Data manipulation and display
- **Requests** - HTTP client for API communication

### Infrastructure

- **Render** - Backend hosting and database
- **Streamlit Cloud** - Frontend deployment
- **GitHub** - Version control and CI/CD

## 🌐 Deployment Links

🔗 **Live App (Streamlit):** [https://splitwise-jsh.streamlit.app](https://splitwise-jsh.streamlit.app)

🔗 **API Base URL:** [https://splitwise-pzwt.onrender.com](https://splitwise-pzwt.onrender.com)

🔗 **API Documentation:** [https://splitwise-pzwt.onrender.com/docs](https://splitwise-pzwt.onrender.com/docs)

## 🧪 How to Test

### Quick Start (5 minutes)

1. **Open the Live App** → [SplitEase App](https://splitwise-jsh.streamlit.app)
2. **Add Your First Expense:**
   - Amount: $60
   - Description: "Dinner at restaurant"
   - Paid by: Your name
   - Participants: Add 2-3 friends
   - Try different split methods!
3. **Check the Dashboard** → See balances and settlements
4. **Explore History** → Filter by person or category

### API Testing

- **Postman Collection:** Import from [API Documentation](https://splitwise-pzwt.onrender.com/docs)
- **Interactive Docs:** Use the built-in FastAPI interface
- **Health Check:** GET `/api/v1/health` to verify system status

## 📁 Project Structure

splitwise/
├── app/                          # FastAPI Backend
│   ├── __init__.py
│   ├── main.py                   # FastAPI app & startup
│   ├── database.py               # Database config & connection
│   ├── models.py                 # SQLAlchemy models
│   ├── schemas.py                # Pydantic schemas
│   ├── crud.py                   # Database operations
│   └── routes.py                 # API endpoints
├── streamlit_app.py              # Streamlit frontend
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
└── README.md                     # Project documentation

## 🛠️ Local Development

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Git

### Setup Steps

1. **Clone Repository**

   ```bash
   git clone https://github.com/yourusername/splitease
   cd splitease
   ```
2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```
3. **Set Environment Variables**

   ```bash
   cp .env.example .env
   # Edit .env with your DATABASE_URL
   ```
4. **Run Backend**

   ```bash
   uvicorn app.main:app --reload
   # API available at http://localhost:8000
   ```
5. **Run Frontend**

   ```bash
   streamlit run streamlit_app.py
   # App available at http://localhost:8501
   ```

## ⚠️ Known Limitations

- **Name Consistency** - Participant names must be exactly the same across expenses
- **Currency Support** - Currently supports single currency (₹ INR)
- **Recurring Expenses** - Manual entry required for recurring bills
- **File Uploads** - Receipt scanning not yet implemented
- **Mobile App** - Web-based only, no native mobile app

## 🔮 Future Enhancements

- 📱 Mobile-responsive PWA
- 🔄 Recurring expense templates
- 📷 Receipt scanning with OCR
- 💱 Multi-currency support
- 👥 User authentication & profiles
- 📧 Email notifications for settlements
- 📊 Advanced analytics & reporting

## 🙌 Acknowledgements

- **Inspired by** [Splitwise](https://splitwise.com) - The gold standard for expense sharing
- **UI/UX Ideas** from Google Pay Bill Split feature
- **Built with** FastAPI, Streamlit, and PostgreSQL
- **Hosted on** Render and Streamlit Cloud

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**Built with ❤️ for seamless expense sharing**

*Made by developers who got tired of calculating who owes what after every group dinner* 🍕💸
