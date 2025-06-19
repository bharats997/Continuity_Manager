import React, { useState, useEffect } from 'react';
import axios from 'axios';

const UserSelector = ({ value, onChange, organizationId, className }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchUsers = async () => {
      if (!organizationId) {
        // setError('Organization ID is required to fetch users.');
        // setUsers([]); // Clear users if org ID is missing
        return; // Or handle as per application's logic for global users if any
      }
      setLoading(true);
      setError(null);
      try {
        // Assuming the API endpoint is /api/v1/users and filters by organization_id query param
        // Adjust if your API uses a different path or method for organization-specific users
        const response = await axios.get(`/api/v1/users?organization_id=${organizationId}`);
        setUsers(response.data.items || response.data); // Adjust based on your API response structure
      } catch (err) {
        console.error('Error fetching users:', err);
        setError(err.response?.data?.detail || err.message || 'Failed to fetch users');
        setUsers([]); // Clear users on error
      }
      setLoading(false);
    };

    fetchUsers();
  }, [organizationId]); // Refetch if organizationId changes

  if (loading) {
    return <p className="text-sm text-gray-500">Loading users...</p>;
  }

  if (error) {
    return <p className="text-sm text-red-500">Error: {error}</p>;
  }
  
  // Add a default "None" or "Select User" option
  const options = [
    <option key="" value="">
      -- Select Department Head --
    </option>,
    ...users.map(user => (
      <option key={user.id} value={user.id}>
        {user.firstName} {user.lastName} ({user.email})
      </option>
    ))
  ];

  return (
    <select
      id="user-selector"
      name="departmentHeadId"
      value={value || ''} // Ensure value is not undefined for controlled component
      onChange={(e) => onChange(e.target.value ? e.target.value : null)} // Pass null if "None" is selected
      className={`mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${className || ''}`}
      disabled={!organizationId || users.length === 0}
    >
      {options}
    </select>
  );
};

export default UserSelector;
