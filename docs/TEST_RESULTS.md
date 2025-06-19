# Test Results

Last Updated: 2025-06-09

## `backend/app/tests/api/test_departments_api.py` (44 tests)

| Test Name                                                       | Status |
| --------------------------------------------------------------- | ------ |
| test_create_department_success                                  | PASSED |
| test_create_department_empty_name                               | PASSED |
| test_create_department_name_too_long                            | PASSED |
| test_create_department_description_too_long                     | PASSED |
| test_create_department_malformed_organization_id                | PASSED |
| test_create_department_malformed_dept_head_id                   | PASSED |
| test_create_department_non_existent_dept_head_id                | PASSED |
| test_create_department_dept_head_id_different_org               | PASSED |
| test_create_department_malformed_location_id                    | PASSED |
| test_create_department_non_existent_location_id                 | PASSED |
| test_create_department_team_members_zero                        | PASSED |
| test_create_department_team_members_negative                    | PASSED |
| test_create_department_team_members_not_integer                 | PASSED |
| test_create_department_duplicate_name_conflict                  | PASSED |
| test_list_departments_empty                                     | PASSED |
| test_list_departments_with_data                                 | PASSED |
| test_update_department_empty_name                               | PASSED |
| test_update_department_name_too_long                            | PASSED |
| test_update_department_description_too_long                     | PASSED |
| test_update_department_malformed_department_head_id             | PASSED |
| test_update_department_non_existent_department_head_id          | PASSED |
| test_update_department_head_id_different_organization           | PASSED |
| test_get_department_by_id_success                               | PASSED |
| test_get_department_by_id_not_found                             | PASSED |
| test_get_department_by_id_with_relations                        | PASSED |
| test_update_department_success                                  | PASSED |
| test_update_department_set_relations                            | PASSED |
| test_update_department_change_relations                         | PASSED |
| test_update_department_clear_relations                          | PASSED |
| test_update_department_not_found                                | PASSED |
| test_update_department_invalid_relations                        | PASSED |
| test_delete_department_success_soft_delete                      | PASSED |
| test_delete_department_not_found_or_already_deleted             | PASSED |
| test_create_department_invalid_name_empty                       | PASSED |
| test_create_department_invalid_name_too_long                    | PASSED |
| test_update_department_invalid_name_empty                       | PASSED |
| test_update_department_invalid_name_too_long                    | PASSED |
| test_create_department_non_existent_organization_id             | PASSED |
| test_create_department_head_different_organization              | PASSED |
| test_update_department_head_different_organization              | PASSED |
| test_create_department_location_different_organization          | PASSED |
| test_update_department_location_different_organization          | PASSED |
| test_department_api_rbac                                        | PASSED |
| test_create_department_with_same_name_as_soft_deleted           | PASSED |

## `backend/app/tests/api/test_applications_api.py` (29 tests)

| Test Name                                                | Status |
| -------------------------------------------------------- | ------ |
| test_create_application                                  | PASSED |
| test_create_application_minimal_data                     | PASSED |
| test_create_application_invalid_organization_id          | PASSED |
| test_create_application_invalid_app_owner_id             | PASSED |
| test_read_application                                    | PASSED |
| test_read_application_not_found                          | PASSED |
| test_read_applications_empty                             | PASSED |
| test_read_applications_list                              | PASSED |
| test_read_applications_pagination_and_filtering          | PASSED |
| test_update_application                                  | PASSED |
| test_update_application_not_found                        | PASSED |
| test_update_application_invalid_owner                    | PASSED |
| test_delete_application                                  | PASSED |
| test_delete_application_not_found                        | PASSED |
| test_delete_already_deleted_application                  | PASSED |

## `backend/app/tests/api/test_locations_api.py` (9 tests)

| Test Name                                           | Status |
| --------------------------------------------------- | ------ |
| test_create_location                                | PASSED |
| test_read_location                                  | PASSED |
| test_read_locations_for_organization                | PASSED |
| test_update_location                                | PASSED |
| test_update_location_not_found                      | PASSED |
| test_delete_location                                | PASSED |
| test_delete_location_not_found                      | PASSED |
| test_create_location_non_existent_org               | PASSED |
| test_create_location_duplicate_name_in_org          | PASSED |

## `backend/app/tests/api/test_people_api.py` (18 tests)

| Test Name                                           | Status |
| --------------------------------------------------- | ------ |
| test_create_person_as_admin                         | PASSED |
| test_create_person_invalid_department_id            | PASSED |
| test_create_person_invalid_location_id              | PASSED |
| test_create_person_with_invalid_role_ids            | PASSED |
| test_create_person_duplicate_email                  | PASSED |
| test_create_person_as_non_admin                     | PASSED |
| test_list_people_as_bcm_manager                     | PASSED |
| test_get_person_by_id_as_admin                      | PASSED |
| test_get_person_not_found                           | PASSED |
| test_update_person_as_admin                         | PASSED |
| test_update_person_not_found                        | PASSED |
| test_soft_delete_person_as_admin                    | PASSED |
| test_soft_delete_person_not_found                   | PASSED |
| test_soft_delete_already_inactive_person            | PASSED |
| test_update_person_duplicate_email                  | PASSED |
| test_update_person_invalid_department_id            | PASSED |
| test_update_person_invalid_location_id              | PASSED |
| test_update_person_invalid_role_ids                 | PASSED |

## `backend/app/tests/api/test_roles_api.py` (11 tests)

| Test Name                                                              | Status |
| ---------------------------------------------------------------------- | ------ |
| test_list_roles_as_bcm_manager                                         | PASSED |
| test_get_role_by_id_as_bcm_manager                                     | PASSED |
| test_get_role_not_found                                                | PASSED |
| test_create_role_as_authorized_user_no_payload_permissions             | PASSED |
| test_create_role_as_authorized_user_with_payload_permissions         | PASSED |
| test_create_role_duplicate_name                                        | PASSED |
| test_create_role_with_invalid_permission_ids                           | PASSED |
| test_create_role_unauthorized_user                                     | PASSED |
| test_update_role_replace_permissions                                   | PASSED |
| test_update_role_remove_all_permissions                                | PASSED |
| test_update_role_permissions_unchanged_if_not_provided                 | PASSED |

## `backend/tests/test_rbac_models.py` (6 tests)

| Test Name                                   | Status |
| ------------------------------------------- | ------ |
| test_create_user                            | PASSED |
| test_create_role                            | PASSED |
| test_create_permission                      | PASSED |
| test_assign_role_to_user                    | PASSED |
| test_assign_permission_to_role              | PASSED |
| test_user_has_permission_through_role       | PASSED |

## `backend/app/tests/api/test_processes_api_rbac.py` (40 tests)

| Test Name                                                              | Status |
| ---------------------------------------------------------------------- | ------ |
| test_rbac_create_process_with_permission                               | PASSED |
| test_rbac_create_process_without_permission                            | PASSED |
| test_rbac_create_process_with_no_relevant_permissions                  | PASSED |
| test_create_process_duplicate_name_in_department                       | PASSED |
| test_create_process_with_location_from_different_organization          | PASSED |
| test_create_process_with_invalid_department_id                         | PASSED |
| test_create_process_with_invalid_owner_id                              | PASSED |
| test_create_process_with_invalid_application_ids                       | PASSED |
| test_create_process_with_invalid_upstream_dependency_ids               | PASSED |
| test_create_process_with_invalid_downstream_dependency_ids             | PASSED |
| test_rbac_read_process_with_permission                                 | PASSED |
| test_rbac_read_process_without_read_permission                         | PASSED |
| test_rbac_read_process_with_no_relevant_permissions                    | PASSED |
| test_rbac_read_process_from_different_organization                     | PASSED |
| test_rbac_update_process_with_permission                               | PASSED |
| test_rbac_update_process_without_update_permission                     | PASSED |
| test_rbac_update_process_with_no_relevant_permissions                  | PASSED |
| test_rbac_update_process_from_different_organization                   | PASSED |
| test_update_process_name_to_duplicate_in_same_department               | PASSED |
| test_update_process_department_to_different_organization               | PASSED |
| test_update_process_owner_to_different_organization                    | PASSED |
| test_update_process_location_from_different_organization               | PASSED |
| test_update_process_application_from_different_organization            | PASSED |
| test_update_process_dependency_from_different_organization             | PASSED |
| test_update_process_with_invalid_foreign_key_department                | PASSED |
| test_update_process_with_invalid_foreign_key_owner                     | PASSED |
| test_update_process_with_invalid_foreign_key_location                  | PASSED |
| test_update_process_with_invalid_foreign_key_application               | PASSED |
| test_update_process_with_invalid_foreign_key_dependency                | PASSED |
| test_update_process_clear_locations                                    | PASSED |
| test_update_process_clear_applications                                 | PASSED |
| test_update_process_clear_upstream_dependencies                        | PASSED |
| test_update_process_clear_downstream_dependencies                      | PASSED |
| test_rbac_delete_process_with_permission                               | PASSED |
| test_rbac_delete_process_without_delete_permission                     | PASSED |
| test_rbac_delete_process_with_no_relevant_permissions                  | PASSED |
| test_rbac_delete_process_from_different_organization                   | PASSED |
| test_rbac_list_processes_with_permission_and_org_scoping               | PASSED |
| test_rbac_list_processes_without_read_permission                       | PASSED |
| test_rbac_list_processes_with_no_relevant_permissions                  | PASSED |

## `backend/app/tests/api/test_processes_api.py` (27 tests)

| Test Name                                         | Status |
| ------------------------------------------------- | ------ |
| test_create_process_success                       | PASSED |
| test_create_process_minimal_data                  | PASSED |
| test_create_process_invalid_department_id         | PASSED |
| test_create_process_invalid_owner_id              | PASSED |
| test_create_process_duplicate_name_in_department  | PASSED |
| test_create_process_invalid_location_id           | PASSED |
| test_create_process_invalid_application_id        | PASSED |
| test_create_process_invalid_dependency_id         | PASSED |
| test_read_process_success                         | PASSED |
| test_read_process_not_found                       | PASSED |
| test_read_process_different_organization          | PASSED |
| test_list_processes_empty                         | PASSED |
| test_list_processes_success                       | PASSED |
| test_list_processes_pagination_and_sorting        | PASSED |
| test_list_processes_filter_by_name                | PASSED |
| test_list_processes_filter_by_department          | PASSED |
| test_list_processes_filter_by_criticality         | PASSED |
| test_update_process_success                       | PASSED |
| test_update_process_clear_m2m_relationships       | PASSED |
| test_update_process_not_found                     | PASSED |
| test_update_process_invalid_department_id         | PASSED |
| test_update_process_name_uniqueness_violation     | PASSED |
| test_update_process_different_organization        | PASSED |
| test_delete_process_success                       | PASSED |
| test_delete_process_not_found                     | PASSED |
| test_delete_process_already_deleted               | PASSED |
| test_delete_process_different_organization        | PASSED |
