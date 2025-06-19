import React, { useState } from 'react';
import UserSelector from '../UserSelector';

const CreateDepartmentModal = ({ onClose, onSubmit, organizationId }) => {
  const [departmentName, setDepartmentName] = useState('');
  const [description, setDescription] = useState('');
  const [departmentHeadId, setDepartmentHeadId] = useState(null); // For UserSelector
  const [parentDepartment, setParentDepartment] = useState(''); // For now, treat as text input for name/ID
  // ... other form fields state

  const handleSubmit = (e) => {
    e.preventDefault();
    const departmentData = { 
      name: departmentName, 
      description: description,
      department_head_id: departmentHeadId, // Use ID from UserSelector
      parent_department_name: parentDepartment // Added parent department name (will map to ID later)
    };
    console.log('Form submitted - from CreateDepartmentModal:', departmentData);
    onSubmit(departmentData); // Call the onSubmit prop passed from parent
    // onClose(); // Parent will handle closing after successful submission/API call
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex justify-center items-center z-50">
      <div className="relative mx-auto p-5 border w-full max-w-lg shadow-lg rounded-md bg-white">
        <div className="mt-3 text-center">
          <h3 className="text-lg leading-6 font-medium font-heading text-gray-900">Create New Department</h3>
          <form onSubmit={handleSubmit} className="mt-2 px-7 py-3 space-y-4">
            {/* Placeholder for form fields */}
            <div className="text-left">
              <label htmlFor="dept-name" className="block text-sm font-medium text-gray-700 font-body">Department Name</label>
              <input 
                type="text" 
                name="dept-name" 
                id="dept-name" 
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-blue focus:border-primary-blue sm:text-sm font-body"
                value={departmentName}
                onChange={(e) => setDepartmentName(e.target.value)}
                placeholder="e.g., Human Resources"
                required
              />
            </div>
            <div className="text-left">
              <label htmlFor="dept-desc" className="block text-sm font-medium text-gray-700 font-body">Description (Optional)</label>
              <textarea 
                name="dept-desc" 
                id="dept-desc" 
                rows="3"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-blue focus:border-primary-blue sm:text-sm font-body"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="A brief description of the department's role and responsibilities."
              />
            </div>
            <div className="text-left">
              <label htmlFor="user-selector" className="block text-sm font-medium text-gray-700 font-body">Department Head</label>
              <UserSelector
                value={departmentHeadId}
                onChange={setDepartmentHeadId}
                organizationId={organizationId}
                className="mt-1"
              />
            </div>
            <div className="text-left">
              <label htmlFor="parent-dept" className="block text-sm font-medium text-gray-700 font-body">Parent Department (Name/ID - Optional)</label>
              <input 
                type="text" 
                name="parent-dept" 
                id="parent-dept" 
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-blue focus:border-primary-blue sm:text-sm font-body"
                value={parentDepartment}
                onChange={(e) => setParentDepartment(e.target.value)}
                placeholder="e.g., Executive Office or leave blank"
              />
            </div>
            {/* Add more form fields here as needed (Head, Parent Dept, etc.) */}
            <div className="items-center px-4 py-3 flex justify-end space-x-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-gray-200 text-gray-800 font-body rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-primary-blue text-white font-body rounded-md shadow hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75 transition-colors"
              >
                Save Department
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateDepartmentModal;
