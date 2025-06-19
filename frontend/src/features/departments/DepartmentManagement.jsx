import React, { useState, useEffect } from 'react';
import CreateDepartmentModal from './CreateDepartmentModal'; // Import the modal
import axios from 'axios'; // Will be used for API calls

const DepartmentManagement = () => {
  // const [departments, setDepartments] = useState([]);
  // const [isLoading, setIsLoading] = useState(false);
  // const [error, setError] = useState(null);
  // const [showCreateModal, setShowCreateModal] = useState(false);
  // const [showEditModal, setShowEditModal] = useState(false);
  // const [currentDepartment, setCurrentDepartment] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Placeholder for API call to fetch departments
  // useEffect(() => {
  //   const fetchDepartments = async () => {
  //     setIsLoading(true);
  //     try {
  //       // const response = await axios.get('/api/v1/departments');
  //       // setDepartments(response.data.items || response.data); // Adjust based on API response
  //     } catch (err) {
  //       setError(err.message || 'Failed to fetch departments');
  //       console.error("Error fetching departments:", err);
  //     }
  //     setIsLoading(false);
  //   };
  //   fetchDepartments();
  // }, []);

  return (
    <div className="bg-white p-6 sm:p-8 rounded-xl shadow-lg">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
        <h2 className="text-2xl sm:text-3xl font-heading text-gray-800 mb-4 sm:mb-0">
          Department Management
        </h2>
        <button 
          className="bg-primary-blue text-white font-body py-2 px-6 rounded-lg shadow hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75"
          onClick={() => setShowCreateModal(true)}
        >
          Add New Department
        </button>
      </div>

      {/* Placeholder for Department Table/List */}
      {/* {isLoading && <p className="text-center text-body text-gray-600 py-4">Loading departments...</p>} */}
      {/* {error && <p className="text-center text-body text-red-600 bg-red-100 p-3 rounded-md">Error: {error}</p>} */}
      {/* {!isLoading && !error && departments.length === 0 && ( */}
      {/*   <p className="text-center text-body text-gray-500 py-4">No departments found. Click 'Add New Department' to create one.</p> */}
      {/* )} */}
      {/* {!isLoading && !error && departments.length > 0 && ( */}
      {/*   <div className="overflow-x-auto"> */}
      {/*     <table className="min-w-full bg-white"> */}
      {/*       <thead className="bg-gray-200"> */}
      {/*         <tr> */}
      {/*           <th className="text-left py-3 px-4 font-heading text-gray-600">Name</th> */}
      {/*           <th className="text-left py-3 px-4 font-heading text-gray-600">Description</th> */}
      {/*           <th className="text-left py-3 px-4 font-heading text-gray-600">Head</th> */}
      {/*           <th className="text-left py-3 px-4 font-heading text-gray-600">Actions</th> */}
      {/*         </tr> */}
      {/*       </thead> */}
      {/*       <tbody className="text-gray-700 font-body"> */}
            {/* Map through departments and render rows */}
      {/*       </tbody> */}
      {/*     </table> */}
      {/*   </div> */}
      {/* )} */}

      <div className="mt-8 p-4 border border-dashed border-gray-300 rounded-md">
        <h3 className="font-heading text-lg text-gray-700 mb-2">Development Plan:</h3>
        <ul className="list-disc list-inside text-body text-gray-600 space-y-1">
          <li>Implement Create Department Modal/Form.</li>
          <li>Implement API call to POST new department.</li>
          <li>Display departments in a responsive table.</li>
          <li>Implement Edit Department Modal/Form with pre-population.</li>
          <li>Implement API call to PUT updated department.</li>
          <li>Implement Delete Department confirmation and API call.</li>
          <li>Add client-side and handle server-side validation.</li>
          <li>Implement pagination and search/filtering for the department list.</li>
          <li>Ensure UI matches PRD guidelines (fonts, colors, minimalist design).</li>
        </ul>
      </div>

      {/* Modals for Create/Edit would go here */}
      {/* Modals for Create/Edit would go here */}
      {showCreateModal && 
        <CreateDepartmentModal 
          onClose={() => setShowCreateModal(false)} 
          onSubmit={async (departmentData) => {
            console.log('Attempting to create department with data:', departmentData);
            try {
              // Adjust parent_department_name: if empty, send null, otherwise send the name.
              // The backend will need to handle resolving this name to an ID or expect an ID directly.
              // For now, we send the name or null if empty.
              const DEFAULT_PLACEHOLDER_ORG_ID = "00000000-0000-0000-0000-000000000001";

              // Construct the payload strictly based on the DepartmentCreate Pydantic model
              const apiPayload = {
                name: departmentData.name,
                description: departmentData.description,
                organizationId: DEFAULT_PLACEHOLDER_ORG_ID,
                department_head_id: null, // departmentData.head is a string name, Pydantic expects Optional[uuid.UUID].
                                          // Setting to null for now. A proper solution would involve a person selector
                                          // that provides the UUID of the department head.
                // location_ids is not included here as it has a default_factory in the Pydantic model,
                // so it will default to an empty list if not provided.
              };
              
              console.log('Final payload being sent to backend:', apiPayload);

              const response = await axios.post('/api/v1/departments/', apiPayload);
              console.log('Department created successfully:', response.data);
              // TODO: Add user feedback (e.g., toast notification)
              // TODO: Refresh department list
              setShowCreateModal(false); // Close modal on success
            } catch (error) {
              console.error('Error creating department:', error.response ? error.response.data : error.message);
              // TODO: Add user feedback for error
            }
          }}
        />
      }
      {/* {showEditModal && currentDepartment && <EditDepartmentModal department={currentDepartment} onClose={() => setShowEditModal(false)} />} */}
    </div>
  );
};

export default DepartmentManagement;
