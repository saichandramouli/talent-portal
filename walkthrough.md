# Walkthrough – Multi-User Logins & Separate Carts for Corporate Clients

We have successfully implemented Option 2 to support **multiple login accounts (users)** associated with a single **Corporate Client profile (company)**, with the added requirement that **each user account has its own separate Shortlist Cart**.

## Changes Implemented

### 1. Database Model Restructuring
- **`accounts/models.py`**: Added a `corporate_client` `ForeignKey` field to link user accounts to client profiles. Also added a `corporate_client_profile` property for backward compatibility.
- **`myspace/models.py`**:
  - Removed the `OneToOneField` mapping `CorporateClient` to `User`.
  - Rebuilt the `CandidateCart` model to reference `User` instead of `CorporateClient` (using `related_name='corporate_cart_items'`).
- **Safe Migrations**: Created a data-migration block in postgres to safely copy existing OneToOne relations into ForeignKeys and transfer active client shortlist items to the individual user accounts without data loss.

### 2. View and Business Logic Updates
- **`myspace/views/client_views.py`**:
  - Rewrote the client profile resolver `_get_corporate_client(user)` to fetch via `user.corporate_client`.
  - Updated all dashboard, cart listing, adding, and removing views to filter shortlist cart items per individual `User` (`user=request.user`) instead of the shared client company profile.
  - Fixed candidate document/resume downloading logic to resolve the client profile via `request.user.corporate_client` instead of referencing the legacy `user` field, resolving a `PermissionDenied` error on download requests.
  - Updated `corporate_candidate_detail` to verify and pass `is_shortlisted` (checking if the candidate is in the current user's cart) in the template context.
- **`myspace/views/admin_views.py`**:
  - Added new admin actions for creating, editing, and toggling active status on users linked to a specific client company.
  - Added a deep delete view (`admin_corporate_client_delete`) that deletes the company profile along with all associated user accounts.

### 3. User Interface Updates
- **`templates/myspace/admin/corporate_client_list.html`**: Displays the count of users for each corporate client and provides a new "Manage Logins" action button.
- **`templates/myspace/admin/corporate_client_form.html`**: Simplified profile editing. When creating a client, the admin enters both the profile details and the primary contact account. When editing, the admin manages the company profile with a button/tab to view and edit individual logins.
- **`templates/myspace/admin/corporate_client_users.html` (NEW)**: Lists all login accounts for a specific client company.
- **`templates/myspace/admin/corporate_client_user_form.html` (NEW)**: Add/edit login accounts for a client company.
- **`templates/myspace/base_myspace.html`**: Updated the topbar cart count badge to read from the user's specific cart (`user.corporate_cart_items.count`).
- **`templates/myspace/client/cart.html`**: Fixed multiline Django template tags for candidate email and phone to ensure proper parsing by the template engine, restoring contact visibility inside the client's shortlist cart. Also optimized row spacing and paddings for a compact layout.
- **`templates/myspace/client/candidate_detail.html`**: Updated button logic to display "Shortlisted" based on `is_shortlisted` (whether the candidate is currently in the active user's cart) instead of checking approved credential requests.

## Verification Results
- Ran `python manage.py check` successfully with **0 issues identified**.
- Migrations executed perfectly with PostgreSQL.
