using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bds.Infrastructure.RealEstate.Migrations
{
    /// <inheritdoc />
    public partial class AddProfileProcedures : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("""
                CREATE OR REPLACE FUNCTION realestate.fn_customer_get_by_id(p_id uuid)
                RETURNS TABLE (id uuid, user_id uuid, full_name varchar, email varchar, phone_number varchar, date_of_birth date, address varchar, created_at timestamptz, updated_at timestamptz)
                LANGUAGE sql STABLE
                AS $$
                    SELECT c.id, c.user_id, c.full_name, c.email, c.phone_number, c.date_of_birth, c.address, c.created_at, c.updated_at
                    FROM realestate.customers c
                    WHERE c.id = p_id;
                $$;

                CREATE OR REPLACE FUNCTION realestate.fn_customer_get_by_user_id(p_user_id uuid)
                RETURNS TABLE (id uuid, user_id uuid, full_name varchar, email varchar, phone_number varchar, date_of_birth date, address varchar, created_at timestamptz, updated_at timestamptz)
                LANGUAGE sql STABLE
                AS $$
                    SELECT c.id, c.user_id, c.full_name, c.email, c.phone_number, c.date_of_birth, c.address, c.created_at, c.updated_at
                    FROM realestate.customers c
                    WHERE c.user_id = p_user_id;
                $$;

                CREATE OR REPLACE FUNCTION realestate.fn_customer_search(
                    p_keyword varchar, p_sort_by varchar, p_descending boolean, p_limit integer, p_offset integer)
                RETURNS TABLE (id uuid, user_id uuid, full_name varchar, email varchar, phone_number varchar, date_of_birth date, address varchar, created_at timestamptz, updated_at timestamptz, total_count bigint)
                LANGUAGE sql STABLE
                AS $$
                    SELECT c.id, c.user_id, c.full_name, c.email, c.phone_number, c.date_of_birth, c.address, c.created_at, c.updated_at, count(*) OVER ()
                    FROM realestate.customers c
                    WHERE p_keyword IS NULL
                       OR c.full_name ILIKE '%' || p_keyword || '%'
                       OR c.email ILIKE '%' || p_keyword || '%'
                       OR c.phone_number ILIKE '%' || p_keyword || '%'
                    ORDER BY
                        CASE WHEN lower(p_sort_by) = 'fullname' AND NOT p_descending THEN c.full_name END ASC,
                        CASE WHEN lower(p_sort_by) = 'fullname' AND p_descending THEN c.full_name END DESC,
                        CASE WHEN coalesce(lower(p_sort_by), 'createdat') <> 'fullname' AND NOT p_descending THEN c.created_at END ASC,
                        CASE WHEN coalesce(lower(p_sort_by), 'createdat') <> 'fullname' AND p_descending THEN c.created_at END DESC,
                        c.id
                    LIMIT p_limit OFFSET p_offset;
                $$;

                -- Creates the profile on first call and updates it afterwards; ON CONFLICT makes concurrent calls safe.
                -- p_result: 0 success.
                CREATE OR REPLACE PROCEDURE realestate.sp_customer_upsert(
                    p_id uuid, p_user_id uuid, p_full_name varchar, p_email varchar, p_phone_number varchar,
                    p_date_of_birth date, p_address varchar, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    INSERT INTO realestate.customers (
                        id, user_id, full_name, email, phone_number, date_of_birth, address, created_at)
                    VALUES (
                        p_id, p_user_id, p_full_name, p_email, p_phone_number, p_date_of_birth, p_address, now())
                    ON CONFLICT (user_id) DO UPDATE
                    SET full_name = EXCLUDED.full_name,
                        email = EXCLUDED.email,
                        phone_number = EXCLUDED.phone_number,
                        date_of_birth = EXCLUDED.date_of_birth,
                        address = EXCLUDED.address,
                        updated_at = now();
                    p_result := 0;
                END;
                $$;

                CREATE OR REPLACE FUNCTION realestate.fn_agent_get_by_id(p_id uuid)
                RETURNS TABLE (id uuid, user_id uuid, full_name varchar, email varchar, phone_number varchar, license_number varchar, created_at timestamptz, updated_at timestamptz)
                LANGUAGE sql STABLE
                AS $$
                    SELECT a.id, a.user_id, a.full_name, a.email, a.phone_number, a.license_number, a.created_at, a.updated_at
                    FROM realestate.agents a
                    WHERE a.id = p_id;
                $$;

                CREATE OR REPLACE FUNCTION realestate.fn_agent_get_by_user_id(p_user_id uuid)
                RETURNS TABLE (id uuid, user_id uuid, full_name varchar, email varchar, phone_number varchar, license_number varchar, created_at timestamptz, updated_at timestamptz)
                LANGUAGE sql STABLE
                AS $$
                    SELECT a.id, a.user_id, a.full_name, a.email, a.phone_number, a.license_number, a.created_at, a.updated_at
                    FROM realestate.agents a
                    WHERE a.user_id = p_user_id;
                $$;

                CREATE OR REPLACE FUNCTION realestate.fn_agent_search(
                    p_keyword varchar, p_sort_by varchar, p_descending boolean, p_limit integer, p_offset integer)
                RETURNS TABLE (id uuid, user_id uuid, full_name varchar, email varchar, phone_number varchar, license_number varchar, created_at timestamptz, updated_at timestamptz, total_count bigint)
                LANGUAGE sql STABLE
                AS $$
                    SELECT a.id, a.user_id, a.full_name, a.email, a.phone_number, a.license_number, a.created_at, a.updated_at, count(*) OVER ()
                    FROM realestate.agents a
                    WHERE p_keyword IS NULL
                       OR a.full_name ILIKE '%' || p_keyword || '%'
                       OR a.email ILIKE '%' || p_keyword || '%'
                       OR a.phone_number ILIKE '%' || p_keyword || '%'
                    ORDER BY
                        CASE WHEN lower(p_sort_by) = 'fullname' AND NOT p_descending THEN a.full_name END ASC,
                        CASE WHEN lower(p_sort_by) = 'fullname' AND p_descending THEN a.full_name END DESC,
                        CASE WHEN coalesce(lower(p_sort_by), 'createdat') <> 'fullname' AND NOT p_descending THEN a.created_at END ASC,
                        CASE WHEN coalesce(lower(p_sort_by), 'createdat') <> 'fullname' AND p_descending THEN a.created_at END DESC,
                        a.id
                    LIMIT p_limit OFFSET p_offset;
                $$;

                -- p_result: 0 success, 2 license number already used by another agent.
                CREATE OR REPLACE PROCEDURE realestate.sp_agent_upsert(
                    p_id uuid, p_user_id uuid, p_full_name varchar, p_email varchar, p_phone_number varchar,
                    p_license_number varchar, INOUT p_result integer DEFAULT NULL)
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    INSERT INTO realestate.agents (
                        id, user_id, full_name, email, phone_number, license_number, created_at)
                    VALUES (
                        p_id, p_user_id, p_full_name, p_email, p_phone_number, p_license_number, now())
                    ON CONFLICT (user_id) DO UPDATE
                    SET full_name = EXCLUDED.full_name,
                        email = EXCLUDED.email,
                        phone_number = EXCLUDED.phone_number,
                        license_number = EXCLUDED.license_number,
                        updated_at = now();
                    p_result := 0;
                EXCEPTION
                    -- user_id conflicts are handled by ON CONFLICT, so this can only be ix_agents_license_number.
                    WHEN unique_violation THEN
                        p_result := 2;
                END;
                $$;
                """);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("""
                DROP PROCEDURE IF EXISTS realestate.sp_agent_upsert(uuid, uuid, varchar, varchar, varchar, varchar, integer);
                DROP FUNCTION IF EXISTS realestate.fn_agent_search(varchar, varchar, boolean, integer, integer);
                DROP FUNCTION IF EXISTS realestate.fn_agent_get_by_user_id(uuid);
                DROP FUNCTION IF EXISTS realestate.fn_agent_get_by_id(uuid);
                DROP PROCEDURE IF EXISTS realestate.sp_customer_upsert(uuid, uuid, varchar, varchar, varchar, date, varchar, integer);
                DROP FUNCTION IF EXISTS realestate.fn_customer_search(varchar, varchar, boolean, integer, integer);
                DROP FUNCTION IF EXISTS realestate.fn_customer_get_by_user_id(uuid);
                DROP FUNCTION IF EXISTS realestate.fn_customer_get_by_id(uuid);
                """);
        }
    }
}
