# Admin Buyers & Sellers Management API

## Overview
This document describes the comprehensive admin API endpoints for managing buyers and sellers in the FarmConnect platform. All endpoints require admin authentication (Bearer token with admin role).

---

## Authentication
All endpoints require an Authorization header with a valid admin token:
```
Authorization: Bearer <admin_token>
```

---

## BUYERS MANAGEMENT ENDPOINTS

### 1. Get All Buyers with Filters
**GET** `/api/admin/buyers`

**Query Parameters:**
- `status` (optional): Filter by status (e.g., "active", "inactive", "deleted")
- `verified` (optional): Filter by verification status (true/false)
- `search` (optional): Search across business_name, contact_person, phone, email

**Example Request:**
```bash
GET /api/admin/buyers?status=active&verified=false&search=John
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "buyers": [
    {
      "id": 1,
      "user_id": "uuid-here",
      "business_name": "John's Farm Supply",
      "contact_person": "John Doe",
      "contact_phone": "+260123456789",
      "contact_email": "john@example.com",
      "commodity": "Maize",
      "location": "Lusaka",
      "max_price": 15.50,
      "min_volume": 100,
      "notes": "Bulk buyer",
      "is_verified": false,
      "rating": 4.0,
      "status": "active",
      "created_at": "2026-05-23T10:00:00"
    }
  ],
  "count": 1
}
```

---

### 2. Get Single Buyer Details
**GET** `/api/admin/buyers/<buyer_id>`

**Example Request:**
```bash
GET /api/admin/buyers/1
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "buyer": {
    "id": 1,
    "user_id": "uuid-here",
    "business_name": "John's Farm Supply",
    "contact_person": "John Doe",
    "contact_phone": "+260123456789",
    "contact_email": "john@example.com",
    "commodity": "Maize",
    "location": "Lusaka",
    "max_price": 15.50,
    "min_volume": 100,
    "notes": "Bulk buyer",
    "is_verified": false,
    "rating": 4.0,
    "status": "active",
    "created_at": "2026-05-23T10:00:00"
  }
}
```

---

### 3. Create New Buyer (Admin)
**POST** `/api/admin/buyers`

**Request Body:**
```json
{
  "business_name": "John's Farm Supply",
  "contact_person": "John Doe",
  "contact_phone": "+260123456789",
  "contact_email": "john@example.com",
  "commodity": "Maize",
  "location": "Lusaka",
  "max_price": 15.50,
  "min_volume": 100,
  "notes": "Bulk buyer",
  "is_verified": false,
  "rating": 4.0,
  "status": "active"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Buyer created successfully",
  "id": 1
}
```

---

### 4. Update Buyer
**PUT** `/api/admin/buyers/<buyer_id>`

**Request Body (all fields optional):**
```json
{
  "business_name": "Updated Farm Supply",
  "contact_person": "Jane Doe",
  "contact_phone": "+260987654321",
  "contact_email": "jane@example.com",
  "commodity": "Tomatoes",
  "location": "Kitwe",
  "max_price": 20.00,
  "min_volume": 50,
  "notes": "Updated notes",
  "is_verified": true,
  "rating": 4.5,
  "status": "active"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Buyer updated successfully"
}
```

---

### 5. Delete Buyer
**DELETE** `/api/admin/buyers/<buyer_id>`

**Response:**
```json
{
  "success": true,
  "message": "Buyer deleted successfully"
}
```

**Note:** This performs a soft delete (status = 'deleted')

---

### 6. Get Pending Buyers (Unverified)
**GET** `/api/admin/buyers/pending`

**Response:**
```json
{
  "success": true,
  "buyers": [...],
  "count": 5
}
```

---

### 7. Verify/Approve Buyer
**POST** `/api/admin/buyers/<buyer_id>/verify`

**Response:**
```json
{
  "success": true,
  "message": "Buyer verified successfully"
}
```

---

### 8. Reject Buyer
**POST** `/api/admin/buyers/<buyer_id>/reject`

**Response:**
```json
{
  "success": true,
  "message": "Buyer rejected successfully"
}
```

---

## SELLERS MANAGEMENT ENDPOINTS

### 1. Get All Sellers with Filters
**GET** `/api/admin/sellers`

**Query Parameters:**
- `status` (optional): Filter by status (e.g., "active", "inactive", "deleted")
- `verified` (optional): Filter by verification status (true/false)
- `search` (optional): Search across farm_name, business_name, contact_person, phone, email

**Example Request:**
```bash
GET /api/admin/sellers?status=active&verified=false
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "sellers": [
    {
      "id": 1,
      "user_id": "uuid-here",
      "farm_name": "Sunshine Farm",
      "business_name": "Sunshine Farm Ltd",
      "contact_person": "Jane Smith",
      "contact_phone": "+260123456789",
      "contact_email": "jane@farm.com",
      "commodity": "Maize",
      "location": "Livingstone",
      "available_volume": 500,
      "price_per_kg": 8.50,
      "notes": "Certified organic",
      "is_verified": false,
      "rating": 4.5,
      "status": "active",
      "created_at": "2026-05-23T09:00:00"
    }
  ],
  "count": 1
}
```

---

### 2. Get Single Seller Details
**GET** `/api/admin/sellers/<seller_id>`

**Response:**
```json
{
  "success": true,
  "seller": {
    "id": 1,
    "user_id": "uuid-here",
    "farm_name": "Sunshine Farm",
    "business_name": "Sunshine Farm Ltd",
    "contact_person": "Jane Smith",
    "contact_phone": "+260123456789",
    "contact_email": "jane@farm.com",
    "commodity": "Maize",
    "location": "Livingstone",
    "available_volume": 500,
    "price_per_kg": 8.50,
    "notes": "Certified organic",
    "is_verified": false,
    "rating": 4.5,
    "status": "active",
    "created_at": "2026-05-23T09:00:00"
  }
}
```

---

### 3. Create New Seller (Admin)
**POST** `/api/admin/sellers`

**Request Body:**
```json
{
  "farm_name": "Sunshine Farm",
  "business_name": "Sunshine Farm Ltd",
  "contact_person": "Jane Smith",
  "contact_phone": "+260123456789",
  "contact_email": "jane@farm.com",
  "commodity": "Maize",
  "location": "Livingstone",
  "available_volume": 500,
  "price_per_kg": 8.50,
  "notes": "Certified organic",
  "is_verified": false,
  "rating": 4.5,
  "status": "active"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Seller created successfully",
  "id": 1
}
```

---

### 4. Update Seller
**PUT** `/api/admin/sellers/<seller_id>`

**Request Body (all fields optional):**
```json
{
  "farm_name": "Updated Farm Name",
  "business_name": "Updated Business Name",
  "contact_person": "John Smith",
  "contact_phone": "+260987654321",
  "contact_email": "john@farm.com",
  "commodity": "Tomatoes",
  "location": "Ndola",
  "available_volume": 1000,
  "price_per_kg": 12.00,
  "notes": "Updated notes",
  "is_verified": true,
  "rating": 5.0,
  "status": "active"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Seller updated successfully"
}
```

---

### 5. Delete Seller
**DELETE** `/api/admin/sellers/<seller_id>`

**Response:**
```json
{
  "success": true,
  "message": "Seller deleted successfully"
}
```

**Note:** This performs a soft delete (status = 'deleted')

---

### 6. Get Pending Sellers (Unverified)
**GET** `/api/admin/sellers/pending`

**Response:**
```json
{
  "success": true,
  "sellers": [...],
  "count": 3
}
```

---

### 7. Verify/Approve Seller
**POST** `/api/admin/sellers/<seller_id>/verify`

**Response:**
```json
{
  "success": true,
  "message": "Seller verified successfully"
}
```

---

### 8. Reject Seller
**POST** `/api/admin/sellers/<seller_id>/reject`

**Response:**
```json
{
  "success": true,
  "message": "Seller rejected successfully"
}
```

---

## SUMMARY OF ALL ENDPOINTS

### Buyers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/buyers` | Get all buyers (with filters) |
| GET | `/api/admin/buyers/<id>` | Get single buyer |
| POST | `/api/admin/buyers` | Create new buyer |
| PUT | `/api/admin/buyers/<id>` | Update buyer |
| DELETE | `/api/admin/buyers/<id>` | Delete buyer (soft) |
| GET | `/api/admin/buyers/pending` | Get unverified buyers |
| POST | `/api/admin/buyers/<id>/verify` | Verify/approve buyer |
| POST | `/api/admin/buyers/<id>/reject` | Reject buyer |

### Sellers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/sellers` | Get all sellers (with filters) |
| GET | `/api/admin/sellers/<id>` | Get single seller |
| POST | `/api/admin/sellers` | Create new seller |
| PUT | `/api/admin/sellers/<id>` | Update seller |
| DELETE | `/api/admin/sellers/<id>` | Delete seller (soft) |
| GET | `/api/admin/sellers/pending` | Get unverified sellers |
| POST | `/api/admin/sellers/<id>/verify` | Verify/approve seller |
| POST | `/api/admin/sellers/<id>/reject` | Reject seller |

---

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Token required"
}
```

### 403 Forbidden (Not Admin)
```json
{
  "error": "Admin access required"
}
```

### 404 Not Found
```json
{
  "error": "Buyer not found"
}
```

### 500 Server Error
```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

---

## Usage Examples

### Example 1: Get all unverified buyers
```bash
curl -X GET "http://localhost:5000/api/admin/buyers?verified=false" \
  -H "Authorization: Bearer <token>"
```

### Example 2: Create a new buyer as admin
```bash
curl -X POST "http://localhost:5000/api/admin/buyers" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Fresh Foods Ltd",
    "contact_person": "John Doe",
    "contact_phone": "+260123456789",
    "contact_email": "john@freshfoods.com",
    "commodity": "Tomatoes",
    "location": "Lusaka",
    "max_price": 20.00,
    "min_volume": 50,
    "is_verified": true,
    "rating": 4.5,
    "status": "active"
  }'
```

### Example 3: Update and verify a seller
```bash
curl -X PUT "http://localhost:5000/api/admin/sellers/1" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "is_verified": true,
    "rating": 5.0
  }'
```

### Example 4: Verify a pending seller
```bash
curl -X POST "http://localhost:5000/api/admin/sellers/1/verify" \
  -H "Authorization: Bearer <token>"
```

---

## Features

✅ **Full CRUD Operations**: Create, Read, Update, Delete buyers and sellers  
✅ **Advanced Filtering**: Filter by status, verification, and search terms  
✅ **Admin Approval Workflow**: Verify or reject pending buyers/sellers  
✅ **Admin Creation**: Create buyers and sellers directly as admin  
✅ **Rating Management**: Admin can set ratings for buyers and sellers  
✅ **Soft Deletes**: Records are marked as deleted, not permanently removed  
✅ **Comprehensive Search**: Search across multiple fields  

---

## Notes

- All timestamps are in ISO 8601 format
- Soft deletes set status to 'deleted', allowing for data recovery
- Admin can override is_verified status and set ratings directly
- Verification workflow is separate from status (active/inactive/deleted)
- All field updates are optional in PUT requests
