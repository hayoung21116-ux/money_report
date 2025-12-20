# Money Report Frontend

This is the React frontend for the Money Report ledger application.

## Getting Started

### Prerequisites

- Node.js (version 14 or higher)
- npm or yarn

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

### Running the Application

1. Start the development server:
   ```bash
   npm start
   ```

2. Open your browser and navigate to `http://localhost:3000`

### Building for Production

To create a production build:
```bash
npm run build
```

## Project Structure

```
frontend/
├── public/                 # Static assets
│   ├── index.html          # Main HTML file
│   └── manifest.json       # PWA manifest
├── src/                    # Source code
│   ├── components/         # React components
│   ├── services/           # API service layer
│   ├── App.js              # Main application component
│   ├── index.js            # Entry point
│   └── index.css           # Global styles
├── package.json            # Project dependencies and scripts
└── README.md               # This file
```

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm run build` - Builds the app for production
- `npm test` - Runs the test suite
- `npm run eject` - Ejects from Create React App (irreversible)

## Features

- Responsive design for mobile and desktop
- Account management
- Transaction tracking
- Investment portfolio tracking
- Financial statistics and charts
- Progressive Web App (PWA) support

## Technologies Used

- React.js
- Styled Components
- Axios for API requests
- React Router for navigation
- Create React App for project setup

## API Integration

The frontend communicates with the backend API running on `http://localhost:8000`. Make sure the backend is running before starting the frontend.

## Responsive Design

The application is designed to work on all device sizes:
- Mobile phones
- Tablets
- Desktop computers
