import React from 'react';
import { ToastContainer } from 'react-toastify';

import { Routes, Route, Link, NavLink } from 'react-router-dom';
import DepartmentManagement from './features/departments/DepartmentManagement';
// Import other feature components here as they are created
// e.g., import PeopleManagement from './features/people/PeopleManagement';

function App() {
  const navLinkClasses = ({ isActive }) => 
    `px-3 py-2 rounded-md text-sm font-medium font-body transition-colors ${isActive ? 'bg-blue-700 text-white' : 'text-blue-100 hover:bg-blue-600 hover:text-white'}`;

  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="colored"
      />
      <nav className="bg-primary-blue text-white shadow-lg">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-xl font-heading font-semibold hover:text-blue-200 transition-colors">
                Continuity Manager
              </Link>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <NavLink to="/" className={navLinkClasses} end>Home</NavLink>
                <NavLink to="/departments" className={navLinkClasses}>Departments</NavLink>
                {/* Add links to other features here */}
                {/* <NavLink to="/people" className={navLinkClasses}>People</NavLink> */}
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-grow container mx-auto p-4 sm:p-6 lg:p-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/departments" element={<DepartmentManagement />} />
          {/* Add routes for other features here */}
          {/* <Route path="/people" element={<PeopleManagement />} /> */}
        </Routes>
      </main>

      <footer className="bg-gray-800 text-white text-center p-4 mt-auto">
        <p className="font-body">&copy; {new Date().getFullYear()} Continuity Manager by CyRAACS. All rights reserved.</p>
      </footer>
    </div>
  );
}

const Home = () => (
  <div className="bg-white p-6 sm:p-8 rounded-xl shadow-lg">
    <h2 className="text-2xl sm:text-3xl font-heading text-gray-800 mb-4">Welcome to the BCMS Portal</h2>
    <p className="text-body text-gray-700 leading-relaxed">
      This is the central hub for managing your organization's business continuity plans and related data.
      Navigate through the modules using the links in the header to manage departments, users, processes, and more.
    </p>
    <p className="text-body text-gray-700 mt-4 leading-relaxed">
      The system is designed to be intuitive and efficient, helping you ensure resilience and preparedness.
    </p>
  </div>
);

export default App;
