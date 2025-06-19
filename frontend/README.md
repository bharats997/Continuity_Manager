# BCMS Frontend

This directory contains the React frontend for the Business Continuity Management System (BCMS).

## Tech Stack

- React
- Tailwind CSS
- Vite (for development and build)
- Axios (for API calls)
- React Router DOM (for routing)

## Getting Started

1.  Navigate to the `frontend` directory:
    ```sh
    cd frontend
    ```
2.  Install dependencies:
    ```sh
    npm install
    # or
    # yarn install
    ```
3.  Start the development server:
    ```sh
    npm run dev
    # or
    # yarn dev
    ```
    This will typically start the app on `http://localhost:3001` (as configured in `vite.config.js`). API requests to `/api/...` will be proxied to `http://localhost:8000/api/...`.

## Project Structure

- `public/`: Static assets (e.g., `vite.svg`).
- `src/`: Source files.
  - `App.jsx`: Main application component with routing setup.
  - `index.css`: Global styles and Tailwind directives.
  - `index.js`: React entry point, wraps App in BrowserRouter.
  - `components/`: Globally reusable UI components (e.g., buttons, inputs) - *to be created*.
  - `features/`: Feature-specific components and logic (e.g., `departments/`, `people/`).
    - `departments/DepartmentManagement.jsx`: Component for managing departments.
  - `services/`: API service integrations (using Axios) - *to be created*.
  - `hooks/`: Custom React hooks - *to be created*.
  - `utils/`: Utility functions - *to be created*.
- `tailwind.config.js`: Tailwind CSS configuration.
- `postcss.config.js`: PostCSS configuration.
- `vite.config.js`: Vite configuration (includes proxy for backend API).

## UI/UX Guidelines (from PRD)

- Primary Colors: Blue (e.g., `#007bff`)
- Heading Font: Outfit
- Body Font: DM Sans
- Style: Minimalist, clean, uncluttered, refreshing.
