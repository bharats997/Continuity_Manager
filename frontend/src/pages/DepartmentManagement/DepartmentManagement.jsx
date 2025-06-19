import React, { useState, useEffect } from 'react';
import CreateDepartmentModal from '../../features/departments/CreateDepartmentModal'; // Adjusted path
import axios from 'axios';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001";

const DepartmentManagementPage = () => {
  const [departments, setDepartments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const fetchDepartments = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/v1/departments/', {
        params: { organizationId: DEFAULT_ORG_ID }
      });
      setDepartments(response.data.items || response.data || []); // Adjust based on actual API response structure
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch departments';
      setError(errorMessage);
      console.error("Error fetching departments:", err);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    fetchDepartments();
  }, []);

  const handleCreateDepartment = async (departmentData) => {
    console.log('Attempting to create department with data:', departmentData);
    try {
      const apiPayload = {
        name: departmentData.name,
        description: departmentData.description,
        organizationId: DEFAULT_ORG_ID,
        department_head_id: departmentData.department_head_id, // Use ID from modal data
      };
      
      console.log('Final payload being sent to backend:', apiPayload);
      const response = await axios.post('/api/v1/departments/', apiPayload);
      toast.success('Department created successfully!');
      setShowCreateModal(false); // Close modal on success
      fetchDepartments(); // Refresh department list
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create department';
      console.error('Error creating department:', errorMessage);
      toast.error(`Error: ${errorMessage}`);
    }
  };

  return (
    <div className="bg-white p-6 sm:p-8 rounded-xl shadow-lg">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
        <h2 className="text-2xl sm:text-3xl font-heading text-gray-800 mb-4 sm:mb-0">
          Department Management
        </h2>
        <button 
          className="bg-primary-blue text-white font-body py-2 px-6 rounded-lg shadow hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75"
          onClick={() => {
            setError(null); // Clear previous errors when opening modal
            setShowCreateModal(true);
          }}
        >
          Add New Department
        </button>
      </div>

      {isLoading && <p className="text-center text-body text-gray-600 py-4">Loading departments...</p>}
      {error && !showCreateModal && <p className="text-center text-body text-red-600 bg-red-100 p-3 rounded-md mb-4">Error: {error}</p>}
      
      {!isLoading && !error && departments.length === 0 && (
        <p className="text-center text-body text-gray-500 py-4">No departments found. Click 'Add New Department' to create one.</p>
      )}
      {!isLoading && departments.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white">
            <thead className="bg-gray-200">
              <tr>
                <th className="text-left py-3 px-4 font-heading text-gray-600">Name</th>
                <th className="text-left py-3 px-4 font-heading text-gray-600">Description</th>
                {/* Add more headers if needed, e.g., Department Head, Actions */}
              </tr>
            </thead>
            <tbody className="text-gray-700 font-body">
              {departments.map(dept => (
                <tr key={dept.id} className="border-b hover:bg-gray-50">
                  <td className="py-3 px-4">{dept.name}</td>
                  <td className="py-3 px-4">{dept.description || '-'}</td>
                  {/* Render more department data or action buttons here */}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreateModal && 
        <CreateDepartmentModal 
          isOpen={showCreateModal} // Ensure modal knows it's open
          onClose={() => setShowCreateModal(false)} 
          onSubmit={handleCreateDepartment}
          organizationId={DEFAULT_ORG_ID} // Pass organizationId to the modal
          // Pass any existing error to the modal if you want to display it there
          // submissionError={error} 
        />
      }
    </div>
  );
};

export default DepartmentManagementPage;
