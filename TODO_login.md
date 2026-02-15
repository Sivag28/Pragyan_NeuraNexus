# Login/Registration System Implementation

## TODO List:
- [x] 1. Create templates/login.html - Login page with registration
- [x] 2. Create static/css/login.css - Unique styling for login page
- [x] 3. Modify app.py - Add authentication routes and user management
- [x] 4. Modify templates/index.html - Add user info and logout in header

## Implementation Steps:
1. First: Create login.html with split-screen design and registration form - ✅ COMPLETE
2. Second: Create login.css with unique, attractive styling - ✅ COMPLETE
3. Third: Update app.py with auth routes and MongoDB user collection - ✅ COMPLETE
4. Fourth: Update index route to require authentication - ✅ COMPLETE

## Features Implemented:
- Split-screen login page with animated medical-themed visuals
- Registration form on the same page (toggle between login/register)
- Password visibility toggle
- Form validation
- Password hashing (SHA-256)
- Session management
- MongoDB user storage
- Authentication check on index route (redirects to login if not authenticated)
- Logout functionality

## Routes:
- GET /login - Login page
- POST /login - Handle login
- POST /register - Handle registration
- POST /logout - Handle logout
- GET /check-auth - Check authentication status

## How to Use:
1. Run the application: python app.py
2. Open http://localhost:5000/
3. You will be redirected to /login
4. Register a new account using the registration form
5. After registration, login with your credentials
6. You will be redirected to the main page
7. To logout, you can call POST /logout
