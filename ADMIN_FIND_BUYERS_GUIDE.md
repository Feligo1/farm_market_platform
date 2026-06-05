# Admin CRUD Management Guide - Find Buyers & Sellers

## Overview
The admin dashboard now includes comprehensive CRUD (Create, Read, Update, Delete) functionality for managing buyers and sellers listings. Admins can perform full management operations directly from the Find Buyers interface.

---

## Admin Features

### 1. **Admin Panel Display**
When an admin user logs in, a dedicated **Admin Management Panel** appears at the top of the content area with three main actions:
- **Create New** - Create new buyer or seller listings
- **Pending Approvals** - Review and approve/reject pending submissions
- **Bulk Actions** - Future bulk operation capabilities

### 2. **Admin Badge**
A red **ADMIN** badge appears in the top navigation bar when logged in as admin.

### 3. **Admin Sidebar Link**
An **Admin Panel** link appears in the sidebar navigation for admins.

---

## CRUD Operations

### **CREATE Operations**

#### Create a New Buyer Listing
1. Click **"Create New"** in the Admin Panel
2. Fill in the form with:
   - Buyer/Business Name
   - Phone Number
   - Commodity Needed
   - Pickup/Buying Location
   - Max Price (ZMW/kg)
   - Minimum Volume (kg)
   - Notes
   - **[ADMIN ONLY]** Rating (1-5)
   - **[ADMIN ONLY]** Verified Status (Yes/No)
3. Click **"Save Buying Request"**

#### Create a New Seller Listing
1. Click **"Create New"** in the Admin Panel
2. Switch to "Sellers" tab
3. Fill in the form with:
   - Farm/Business Name
   - Phone Number
   - Commodity Available
   - Produce Location
   - Price (ZMW/kg)
   - Available Volume (kg)
   - Notes
   - **[ADMIN ONLY]** Rating (1-5)
   - **[ADMIN ONLY]** Verified Status (Yes/No)
4. Click **"Save Selling Offer"**

### **READ Operations**

#### View All Buyers/Sellers
- Navigate to the appropriate tab (Buyers or Sellers)
- All listings are displayed in either grid or table view
- Use filters to narrow down:
  - Search by name, location, or notes
  - Filter by commodity
  - Filter by location
  - Sort by various criteria

#### View Pending Approvals
1. Click **"Pending Approvals"** in Admin Panel
2. A modal shows all unverified buyer and seller listings
3. Click **"Review"** on any listing to see full details and approval options

#### View Individual Listing
- Click on any card in grid view to see details
- For table view, all details are visible in the table

### **UPDATE Operations**

#### Edit a Listing
1. Hover over a listing card or locate it in table view
2. Click the **Edit** button (pencil icon)
3. Modal opens with current information pre-filled
4. Update the desired fields:
   - Business/Farm name
   - Contact information
   - Commodity
   - Location
   - Price/Volume
   - Notes
   - **[ADMIN ONLY]** Rating
   - **[ADMIN ONLY]** Verified status
5. Click **"Save"** to update

#### Verify/Approve a Listing
1. Find an unverified listing (shows "Pending" badge)
2. Click the **Green Checkmark** button on the card/row
3. A verification modal opens showing:
   - Full listing details
   - Approve button
   - Reject button
4. Review the information and click **"Approve"** to verify

#### Reject a Listing
1. Click the **Green Checkmark** button on an unverified listing
2. In the verification modal, click **"Reject"**
3. Listing status changes to inactive

### **DELETE Operations**

#### Soft Delete a Listing
1. Find the listing you want to delete
2. Click the **Delete** button (trash icon)
3. Confirm deletion in the prompt
4. Listing is marked as deleted (soft delete)
   - Data is preserved in database
   - Listing no longer appears in public view

---

## Admin-Specific Features

### **Approval Workflow**

The platform has a two-step approval process:

1. **Submission** - Users or admins create listings
2. **Verification** - Admins review and approve/reject

**Pending Status Indicators:**
- Unverified listings show a **yellow "Pending" badge**
- Verified listings show a **green "Verified" badge**

### **Admin-Only Fields**

When creating or editing as an admin, you have access to:
- **Rating** - Set initial rating (1-5 stars)
- **Verified** - Directly set verification status

### **Bulk Approvals**

Access the **Pending Approvals** modal to:
- See count of pending buyers and sellers
- Quickly review all pending submissions
- Approve or reject each one individually

---

## Integration with Backend API

The frontend uses the following admin endpoints:

### Buyers Management
- `GET /api/admin/buyers` - List all buyers
- `GET /api/admin/buyers/<id>` - Get single buyer
- `POST /api/admin/buyers` - Create buyer
- `PUT /api/admin/buyers/<id>` - Update buyer
- `DELETE /api/admin/buyers/<id>` - Delete buyer
- `POST /api/admin/buyers/<id>/verify` - Approve buyer
- `POST /api/admin/buyers/<id>/reject` - Reject buyer

### Sellers Management
- `GET /api/admin/sellers` - List all sellers
- `GET /api/admin/sellers/<id>` - Get single seller
- `POST /api/admin/sellers` - Create seller
- `PUT /api/admin/sellers/<id>` - Update seller
- `DELETE /api/admin/sellers/<id>` - Delete seller
- `POST /api/admin/sellers/<id>/verify` - Approve seller
- `POST /api/admin/sellers/<id>/reject` - Reject seller

---

## View Modes

### Grid View (Default)
- Visual card-based display
- Shows all key information
- Hover effects for better visibility
- Best for quick scanning

### Table View
- Structured tabular format
- Columns for all key fields
- Good for bulk operations
- Sortable columns

Switch between views using the toggle buttons in the toolbar.

---

## Search & Filter

### Search
- Type in the search box to filter by:
  - Business/Farm name
  - Location
  - Notes
  - Real-time results

### Filter by Commodity
- Select from dropdown with all available commodities
- Automatically updated based on listed items

### Filter by Location
- Select from locations represented in current listings
- Updates as you filter by other criteria

### Sort Options
- **Newest First** - Most recent listings
- **Price: High to Low** - Highest priced first
- **Price: Low to High** - Lowest priced first
- **Volume: High to Low** - Largest quantities first
- **Name: A to Z** - Alphabetical order

### Reset Filters
- Click **"Reset"** button to clear all filters
- Returns to showing all listings

---

## Statistics Dashboard

At the top of the page, four stat cards show:
- **Buying Requests** - Total number of buyer listings
- **Selling Offers** - Total number of seller listings
- **Verified** - Count of verified listings in current view
- **Locations** - Number of unique locations represented

---

## User Actions (Non-Admin)

Users can:
- View public listings
- Search and filter
- Contact listing owners via message
- Call or WhatsApp sellers/buyers
- Post their own listings (after login)

---

## Export Data

### CSV Export
1. Click the **"Export"** button in toolbar
2. Selects current filtered view
3. Downloads as CSV file with columns:
   - Name, Phone, Commodity, Location
   - Price/Max Price, Volume, Notes, Verified Status

---

## Tips & Best Practices

### Admin Tips
1. **Regular Reviews** - Check pending approvals regularly
2. **Consistent Verification** - Set clear standards for approval
3. **Rating Management** - Use ratings to indicate list quality
4. **Bulk Approvals** - Use the pending panel for efficiency
5. **Data Quality** - Edit listings to maintain data consistency

### For Users
1. **Complete Information** - Fill all fields for better visibility
2. **Clear Notes** - Add specific requirements or details
3. **Accurate Pricing** - Keep prices current and accurate
4. **Update Regularly** - Refresh listings to show active status

---

## Troubleshooting

### Listings Not Appearing
- Check filters (status, commodity, location)
- Verify not in deleted status
- Try resetting filters
- Refresh page (Ctrl+R)

### Cannot Approve/Reject
- Verify you're logged in as admin
- Check internet connection
- Try refreshing the page
- Contact system administrator

### Approval Not Working
- Ensure listing has all required fields
- Check that you have admin privileges
- Verify API endpoint is accessible

---

## Database Connection

All operations are connected to the PostgreSQL database via:
- **API Endpoint**: Flask backend at `/api/admin/*`
- **Authentication**: Bearer token authentication
- **Data Validation**: Server-side validation
- **Status Management**: Active/Inactive/Deleted states

The database maintains:
- Full transaction history
- Audit trails (created_at, updated_at)
- Verification status
- Rating information
- Soft delete preservation

---

## Performance Notes

- Large datasets (1000+) load efficiently
- Real-time search/filter
- Cached commodity and location lists
- Auto-refresh every 60 seconds
- Manual refresh available
- Export handles large datasets

---

## Security

- **Admin-only endpoints** require authentication
- **Bearer token validation** on all requests
- **Role-based access control** checks
- **SQL injection prevention** via parameterized queries
- **CSRF protection** via request headers

---

## Future Enhancements

Planned features:
- Bulk status updates
- Advanced filtering by date range
- Admin notes/comments system
- Listing performance analytics
- Automated expiration workflow
- Email notifications for approvals
