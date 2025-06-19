"""rename_person_to_user_and_update_relations

Revision ID: d1d332415966
Revises: 0a68b7c32f1f
Create Date: 2025-06-05 18:52:49.759491

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1d332415966'
down_revision: Union[str, None] = '0a68b7c32f1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SET foreign_key_checks = 0;")
    try:
        # List of foreign keys to update: (table, column, old_fk_name_guess, new_fk_name_guess, ondelete_policy, referenced_table_old, referenced_table_new)
        # IMPORTANT: old_fk_name_guess must match your database!
        foreign_keys_to_update_details = [
            ('departments', 'department_head_id', 'fk_departments_department_head_id_people', 'fk_departments_department_head_id_users', 'SET NULL'),
            # Uncomment and adjust if these audit columns and their FKs exist
            # ('departments', 'created_by_id', 'fk_departments_created_by_id_people', 'fk_departments_created_by_id_users', 'SET NULL'),
            # ('departments', 'updated_by_id', 'fk_departments_updated_by_id_people', 'fk_departments_updated_by_id_users', 'SET NULL'),
            ('applications', 'appOwnerId', 'fk_applications_app_owner_id_people', 'fk_applications_app_owner_id_users', 'SET NULL'), # Changed app_owner_id to appOwnerId
            # ('applications', 'created_by_id', 'fk_applications_created_by_id_people', 'fk_applications_created_by_id_users', 'SET NULL'),
            # ('applications', 'updated_by_id', 'fk_applications_updated_by_id_people', 'fk_applications_updated_by_id_users', 'SET NULL'),
        ]

        assoc_old_table = 'people_roles'
        assoc_new_table = 'user_roles'
        assoc_old_col = 'personId'
        assoc_new_col = 'user_id'
        assoc_old_fk_name = 'fk_people_roles_personId_people' # GUESS: e.g., people_roles_personId_fkey
        assoc_new_fk_name = 'fk_user_roles_user_id_users'     # GUESS: e.g., user_roles_user_id_fkey
        assoc_ondelete = 'CASCADE'

        # 1. Drop old foreign keys
        for table, col, old_fk, _, _, in foreign_keys_to_update_details:
            try:
                op.drop_constraint(old_fk, table, type_='foreignkey')
            except Exception as e:
                print(f"Skipping drop of non-existent or misnamed constraint {old_fk} on {table}.{col}: {e}")
        
        try:
            op.drop_constraint(assoc_old_fk_name, assoc_old_table, type_='foreignkey')
        except Exception as e:
            print(f"Skipping drop of non-existent or misnamed constraint {assoc_old_fk_name} on {assoc_old_table}.{assoc_old_col}: {e}")

        # 2. Rename tables
        conn = op.get_bind()
        inspector = sa.inspect(conn)

        try:
            op.rename_table('people', 'users')
            print("Renamed table 'people' to 'users'.")
        except sa.exc.DBAPIError as e:
            if hasattr(e.orig, 'args') and e.orig.args[0] == 1146 and ".people'" in str(e.orig.args[1]).lower():
                print("Table 'people' does not exist. Checking for 'users' table...")
                if inspector.has_table('users'):
                    print("'users' table found. Assuming 'people' was already renamed.")
                else:
                    raise Exception("Critical: 'people' table does not exist, and 'users' table also does not exist. Cannot proceed.") from e
            else:
                raise # Re-raise other DBAPI errors

        try:
            op.rename_table(assoc_old_table, assoc_new_table) # assoc_old_table is 'people_roles'
            print(f"Renamed table '{assoc_old_table}' to '{assoc_new_table}'.")
        except sa.exc.DBAPIError as e:
            if hasattr(e.orig, 'args') and e.orig.args[0] == 1146 and f".{assoc_old_table}'".lower() in str(e.orig.args[1]).lower():
                print(f"Table '{assoc_old_table}' does not exist. Checking for '{assoc_new_table}' table...")
                if inspector.has_table(assoc_new_table):
                    print(f"'{assoc_new_table}' table found. Assuming '{assoc_old_table}' was already renamed.")
                else:
                    raise Exception(f"Critical: '{assoc_old_table}' table does not exist, and '{assoc_new_table}' table also does not exist. Cannot proceed.") from e
            else:
                raise

        # 3. Rename column in the (now) user_roles table
        try:
            op.alter_column(assoc_new_table, assoc_old_col, new_column_name=assoc_new_col, existing_type=sa.CHAR(36), nullable=False)
            print(f"Renamed column '{assoc_old_col}' to '{assoc_new_col}' in table '{assoc_new_table}'.")
        except sa.exc.DBAPIError as e:
            if hasattr(e.orig, 'args') and e.orig.args[0] == 1054 and f"unknown column '{assoc_old_col.lower()}'" in str(e.orig.args[1]).lower():
                print(f"Column '{assoc_old_col}' not found in '{assoc_new_table}'. Checking for existing column '{assoc_new_col}'...")
                table_columns = [col['name'] for col in inspector.get_columns(assoc_new_table)]
                if assoc_new_col in table_columns:
                    print(f"Column '{assoc_new_col}' already exists in '{assoc_new_table}'. Assuming rename was done.")
                else:
                    raise Exception(f"Critical: Column '{assoc_old_col}' not found, and column '{assoc_new_col}' also not found in '{assoc_new_table}'. Cannot proceed.") from e
            else:
                raise

        # 4. Recreate foreign keys pointing to 'users' table
        for table, col, _, new_fk, ondelete_pol in foreign_keys_to_update_details:
            try:
                op.create_foreign_key(new_fk, table, 'users', [col], ['id'], ondelete=ondelete_pol)
                print(f"Created foreign key '{new_fk}' on {table}.{col} referencing users.id")
            except sa.exc.OperationalError as e:
                if hasattr(e.orig, 'args') and e.orig.args[0] == 1826: # MySQL error code for duplicate FK name
                    print(f"Foreign key '{new_fk}' on {table}.{col} already exists. Skipping creation.")
                else:
                    raise
        
        try:
            op.create_foreign_key(assoc_new_fk_name, assoc_new_table, 'users', [assoc_new_col], ['id'], ondelete=assoc_ondelete)
            print(f"Created foreign key '{assoc_new_fk_name}' on {assoc_new_table}.{assoc_new_col} referencing users.id")
        except sa.exc.OperationalError as e:
            if hasattr(e.orig, 'args') and e.orig.args[0] == 1826:
                print(f"Foreign key '{assoc_new_fk_name}' on {assoc_new_table}.{assoc_new_col} already exists. Skipping creation.")
            else:
                raise

    finally:
        op.execute("SET foreign_key_checks = 1;")

def downgrade() -> None:
    op.execute("SET foreign_key_checks = 0;")
    try:
        foreign_keys_to_update_details = [
            ('departments', 'department_head_id', 'fk_departments_department_head_id_people', 'fk_departments_department_head_id_users', 'SET NULL'),
            # ('departments', 'created_by_id', 'fk_departments_created_by_id_people', 'fk_departments_created_by_id_users', 'SET NULL'),
            # ('departments', 'updated_by_id', 'fk_departments_updated_by_id_people', 'fk_departments_updated_by_id_users', 'SET NULL'),
            ('applications', 'appOwnerId', 'fk_applications_app_owner_id_people', 'fk_applications_app_owner_id_users', 'SET NULL'), # Changed app_owner_id to appOwnerId
            # ('applications', 'created_by_id', 'fk_applications_created_by_id_people', 'fk_applications_created_by_id_users', 'SET NULL'),
            # ('applications', 'updated_by_id', 'fk_applications_updated_by_id_people', 'fk_applications_updated_by_id_users', 'SET NULL'),
        ]

        assoc_old_table = 'people_roles'
        assoc_new_table = 'user_roles'
        assoc_old_col = 'personId'
        assoc_new_col = 'user_id'
        assoc_old_fk_name = 'fk_people_roles_personId_people'
        assoc_new_fk_name = 'fk_user_roles_user_id_users'
        assoc_ondelete = 'CASCADE'

        # 1. Drop new foreign keys
        for table, col, _, new_fk, _ in foreign_keys_to_update_details:
            try:
                op.drop_constraint(new_fk, table, type_='foreignkey')
            except Exception as e:
                print(f"Skipping drop of non-existent or misnamed constraint {new_fk} on {table}.{col}: {e}")

        try:
            op.drop_constraint(assoc_new_fk_name, assoc_new_table, type_='foreignkey')
        except Exception as e:
            print(f"Skipping drop of non-existent or misnamed constraint {assoc_new_fk_name} on {assoc_new_table}.{assoc_new_col}: {e}")

        # 2. Rename column in user_roles back to personId
        try:
            op.alter_column(assoc_new_table, assoc_new_col, new_column_name=assoc_old_col, existing_type=sa.CHAR(36), nullable=False)
            print(f"Downgrade: Renamed column '{assoc_new_col}' to '{assoc_old_col}' in table '{assoc_new_table}'.")
        except sa.exc.DBAPIError as e:
            if hasattr(e.orig, 'args') and e.orig.args[0] == 1054 and f"unknown column '{assoc_new_col.lower()}'" in str(e.orig.args[1]).lower():
                print(f"Downgrade: Column '{assoc_new_col}' not found in '{assoc_new_table}'. Checking for existing column '{assoc_old_col}'...")
                table_columns = [col['name'] for col in inspector.get_columns(assoc_new_table)] # inspector is defined earlier in downgrade
                if assoc_old_col in table_columns:
                    print(f"Downgrade: Column '{assoc_old_col}' already exists in '{assoc_new_table}'. Assuming rename was done or column was not '{assoc_new_col}'.")
                else:
                    raise Exception(f"Critical (downgrade): Column '{assoc_new_col}' not found, and column '{assoc_old_col}' also not found in '{assoc_new_table}'. Cannot proceed.") from e
            else:
                raise

        # 3. Rename tables back
        conn = op.get_bind()
        inspector = sa.inspect(conn)

        try:
            op.rename_table(assoc_new_table, assoc_old_table) # assoc_new_table is 'user_roles'
            print(f"Downgrade: Renamed table '{assoc_new_table}' to '{assoc_old_table}'.")
        except sa.exc.DBAPIError as e:
            if hasattr(e.orig, 'args') and e.orig.args[0] == 1146 and f".{assoc_new_table}'".lower() in str(e.orig.args[1]).lower():
                print(f"Downgrade: Table '{assoc_new_table}' does not exist. Checking for '{assoc_old_table}' table...")
                if inspector.has_table(assoc_old_table):
                    print(f"Downgrade: '{assoc_old_table}' table found. Assuming '{assoc_new_table}' was already renamed or did not exist.")
                else:
                    raise Exception(f"Critical (downgrade): '{assoc_new_table}' table does not exist, and '{assoc_old_table}' table also does not exist. Cannot proceed.") from e
            else:
                raise

        try:
            op.rename_table('users', 'people')
            print("Downgrade: Renamed table 'users' to 'people'.")
        except sa.exc.DBAPIError as e:
            if hasattr(e.orig, 'args') and e.orig.args[0] == 1146 and ".users'" in str(e.orig.args[1]).lower():
                print("Downgrade: Table 'users' does not exist. Checking for 'people' table...")
                if inspector.has_table('people'):
                    print("Downgrade: 'people' table found. Assuming 'users' was already renamed or did not exist.")
                else:
                    raise Exception("Critical (downgrade): 'users' table does not exist, and 'people' table also does not exist. Cannot proceed.") from e
            else:
                raise

        # 4. Recreate old foreign keys pointing to 'people' table
        for table, col, old_fk, _, ondelete_pol in foreign_keys_to_update_details:
            try:
                op.create_foreign_key(old_fk, table, 'people', [col], ['id'], ondelete=ondelete_pol)
                print(f"Downgrade: Created foreign key '{old_fk}' on {table}.{col} referencing people.id")
            except sa.exc.OperationalError as e:
                if hasattr(e.orig, 'args') and e.orig.args[0] == 1826: # MySQL error code for duplicate FK name
                    print(f"Downgrade: Foreign key '{old_fk}' on {table}.{col} already exists. Skipping creation.")
                else:
                    raise
        
        try:
            op.create_foreign_key(assoc_old_fk_name, assoc_old_table, 'people', [assoc_old_col], ['id'], ondelete=assoc_ondelete)
            print(f"Downgrade: Created foreign key '{assoc_old_fk_name}' on {assoc_old_table}.{assoc_old_col} referencing people.id")
        except sa.exc.OperationalError as e:
            if hasattr(e.orig, 'args') and e.orig.args[0] == 1826:
                print(f"Downgrade: Foreign key '{assoc_old_fk_name}' on {assoc_old_table}.{assoc_old_col} already exists. Skipping creation.")
            else:
                raise

    finally:
        op.execute("SET foreign_key_checks = 1;")
