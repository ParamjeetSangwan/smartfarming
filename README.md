 Click on Link :- https://web-production-e9366.up.railway.app

# SmartFarming 🌱

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Django](https://img.shields.io/badge/Django-5.2.5-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

A comprehensive Django-based smart agriculture platform that empowers farmers with AI-driven insights, resource management, marketplace integration, and data-driven decision-making tools.

---

## 📋 Table of Contents
- [About](#about)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

---

## 🌾 About
SmartFarming is a full-featured web application designed to help farmers:
- Monitor crop health and growth
- Access AI-powered crop recommendations
- Manage farming tools and resources
- Buy/sell agri-products in an integrated marketplace
- Track weather patterns and forecasts
- View government schemes and subsidies
- Manage orders and transactions

Built with Django 5.2.5 and designed for scalability, this platform bridges the gap between traditional farming and modern technology.

---

## ✨ Features
- **Crop Management**: Monitor and manage multiple crops with detailed analytics
- **AI Recommendations**: Smart crop suggestions and advisory based on data
- **Marketplace**: Buy/sell farming tools, seeds, pesticides, and fertilizers
- **Weather Integration**: Real-time weather data and forecasting
- **Order Management**: Complete order tracking and history
- **Admin Dashboard**: Comprehensive analytics and user management
- **User Authentication**: Secure login with 2FA and OTP support
- **Government Schemes**: Information on available farming subsidies
- **Multi-language Support**: Hindi language support for wider reach
- **Responsive Design**: Mobile-friendly interface

---

## 🛠️ Tech Stack
- **Backend**: Django 5.2.5 (Python 3.13)
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Frontend**: HTML5, CSS3, JavaScript
- **Payment Gateway**: Razorpay, UPI
- **APIs**: 
  - OpenRouter (AI Recommendations)
  - OpenWeather API
  - Google OAuth (Authentication)
- **Hosting**: Heroku-ready (Procfile included)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- pip or conda
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/smartfarming.git
   cd smartfarming
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Load initial data** (optional):
   ```bash
   python manage.py load_pesticides
   python manage.py setup_initial_data
   ```

8. **Start development server**:
   ```bash
   python manage.py runserver
   ```

Access the application at `http://localhost:8000`

---

## 📁 Project Structure

```
smartfarming/
├── apps/                          # Django applications
│   ├── admin_panel/              # Admin dashboard
│   ├── ai_recommendations/       # AI-powered crop suggestions
│   ├── crops/                    # Crop management
│   ├── government_schemes/       # Subsidy information
│   ├── marketplace/              # Product marketplace
│   ├── orders/                   # Order management
│   ├── users/                    # User authentication & profiles
│   └── weather/                  # Weather integration
├── smartfarm/                     # Project configuration
├── templates/                     # HTML templates
├── static/                        # CSS, JavaScript, images
├── locale/                        # i18n translations
├── manage.py                      # Django management
└── requirements.txt               # Python dependencies
```

---

## ⚙️ Configuration

### Environment Variables (.env)
Required environment variables:
```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database (optional - defaults to SQLite)
DATABASE_URL=postgresql://user:password@localhost:5432/smartfarm

# External APIs
WEATHER_API_KEY=your-weather-api-key
OPENROUTER_API_KEY=your-openrouter-api-key

# Payment Gateway
RAZORPAY_KEY_ID=your-razorpay-id
RAZORPAY_KEY_SECRET=your-razorpay-secret

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

See `.env.example` for reference.

---

## 📊 API Endpoints

### Crops
- `GET /api/crops/` - List all crops
- `POST /api/crops/` - Create new crop
- `GET /api/crops/<id>/` - Get crop details
- `PUT /api/crops/<id>/` - Update crop
- `DELETE /api/crops/<id>/` - Delete crop

### Marketplace
- `GET /api/marketplace/` - List products
- `POST /api/marketplace/cart/` - Add to cart
- `POST /api/marketplace/checkout/` - Process order

### Weather
- `GET /api/weather/` - Get weather data
- `GET /api/weather/forecast/` - Get forecast

### Users
- `POST /api/users/register/` - Register new user
- `POST /api/users/login/` - User login
- `GET /api/users/profile/` - Get user profile

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👨‍💼 Author

**Developed by**: Smart Farming Team

## 📧 Contact & Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

## 🎯 Future Enhancements

- [ ] Mobile app (React Native)
- [ ] Advanced analytics and reporting
- [ ] IoT sensor integration
- [ ] Real-time notifications
- [ ] Machine learning predictions
- [ ] Community forum

---

**Happy Farming! 🚜**

3. (Optional) Create and activate a virtual environment:
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows

4. Install the required packages:
   pip install -r requirements.txt

5. Apply migrations:
   python manage.py migrate

6. Run the development server:
   python manage.py runserver

7. Open your browser and go to http://127.0.0.1:8000/ to access the dashboard.

---

## Technologies Used
- Python 3.x
- Django 4.2
- HTML / CSS / JavaScript
- SQLite (or your preferred database)
- Pandas / NumPy (for data analysis)
- Bootstrap (optional for UI styling)

---

## Contributing
Contributions are welcome!

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-name`).
3. Make your changes and commit (`git commit -m 'Add feature'`).
4. Push to the branch (`git push origin feature-name`).
5. Open a Pull Request.

---

## License
This project is licensed under the **MIT License**.
---

This version fixes:  
- Fully GitHub-friendly **anchors**  
- **Detailed local setup instructions**  
- **Numbered features list** for clarity  
- Notes about screenshots and database  
- Consistent formatting  
