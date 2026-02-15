# Backend URL Update Task

## Task: Replace existing backend API with https://pragyan-neuranexus.onrender.com

## Files to Update:
- [ ] 1. static/js/script.js
- [ ] 2. static/js/dashboard.js
- [ ] 3. static/js/dashboard-new.js
- [ ] 4. static/js/chatbot.js
- [ ] 5. frontend/js/script.js
- [ ] 6. frontend/js/dashboard.js
- [ ] 7. frontend/js/dashboard-new.js
- [ ] 8. frontend/js/chatbot.js

## Changes to make in each file:
1. Add `const API_BASE_URL = 'https://pragyan-neuranexus.onrender.com';` at the top
2. Replace relative URLs like `/predict` with `${API_BASE_URL}/predict`
