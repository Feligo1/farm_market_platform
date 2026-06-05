# API Documentation

## Base URL
`https://api.farmmarket.zm/api`

## Authentication
All endpoints require Bearer token:
`Authorization: Bearer <session_token>`

## Endpoints

### GET /api/prices
Returns current market prices

### POST /api/add-price
Add new price entry (traders only)

### GET /api/forecast
Get price predictions

## Rate Limiting
100 requests per hour per user