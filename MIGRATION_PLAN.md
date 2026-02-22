Migration plan for `User.username` length change

Summary
- The `User.username` column was previously limited to 12 characters. To avoid breaking existing accounts, the model has been updated to `String(80)`.

Steps before applying DB migrations
1. Run the validation script to detect existing long usernames:

   ```bash
   python3 scripts/check_usernames.py --limit 80
   ```

2. If the script reports any usernames longer than 80, decide how to handle them:
   - Option A (preferred): Contact users and request a shorter username, or programmatically map to a safe new username (e.g., append a numeric suffix) and record mappings.
   - Option B: Truncate usernames in a controlled migration and store original usernames in a separate mapping table for audit/recovery.

3. Create an explicit migration (Alembic or your migration tool) that performs any necessary transformations before altering the schema. The migration should:
   - Add a `username_backup` column or a mapping table if you plan to preserve originals.
   - For each user with username length > 80, either update to the agreed new username or truncate and insert a mapping record.
   - Alter the `username` column type/length to 80.

4. Run the migration in a staging environment, verify user logins, and then deploy to production during a maintenance window if needed.

Notes
- Keep the `app/models.py` `User.username` length consistent with the migration.
- Prefer preserving original data when possible and make mappings explicit and reversible.
