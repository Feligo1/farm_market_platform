# logistics_module.py
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random
import math

class LogisticsModule:
    """Comprehensive logistics and delivery management system"""
    
    def __init__(self, db_path="farm_market.db"):
        self.db_path = db_path
        self.earth_radius_km = 6371.0
        
    # ========== CORE FUNCTIONS ==========
    
    def create_delivery_request(self, request_data: Dict) -> Dict:
        """Create a new delivery request"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Generate unique request ID
            request_id = f"DR{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
            
            # Calculate distance if coordinates provided
            distance = None
            if (request_data.get('pickup_lat') and request_data.get('pickup_lon') and
                request_data.get('delivery_lat') and request_data.get('delivery_lon')):
                distance = self.calculate_distance(
                    request_data['pickup_lat'], request_data['pickup_lon'],
                    request_data['delivery_lat'], request_data['delivery_lon']
                )
            
            # Estimate price
            quoted_price = self.estimate_delivery_price(
                distance or 50,  # Default 50km if no coordinates
                request_data['quantity'],
                request_data.get('commodity', 'general'),
                request_data.get('temperature_required', False)
            )
            
            # Insert delivery request
            cur.execute('''
                INSERT INTO delivery_requests 
                (request_id, farmer_id, farmer_name, farmer_phone, pickup_location,
                 pickup_lat, pickup_lon, delivery_location, delivery_lat, delivery_lon,
                 commodity, quantity, packaging_type, quality_grade, temperature_required,
                 min_temperature, max_temperature, pickup_date, delivery_deadline, budget,
                 status, quoted_price, distance_km, estimated_duration_min, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request_id,
                request_data['farmer_id'],
                request_data.get('farmer_name', ''),
                request_data.get('farmer_phone', ''),
                request_data['pickup_location'],
                request_data.get('pickup_lat'),
                request_data.get('pickup_lon'),
                request_data['delivery_location'],
                request_data.get('delivery_lat'),
                request_data.get('delivery_lon'),
                request_data['commodity'],
                request_data['quantity'],
                request_data.get('packaging_type', 'bags'),
                request_data.get('quality_grade', 'Grade B'),
                request_data.get('temperature_required', False),
                request_data.get('min_temperature'),
                request_data.get('max_temperature'),
                request_data['pickup_date'],
                request_data.get('delivery_deadline'),
                request_data.get('budget'),
                'pending',
                quoted_price,
                distance,
                self.estimate_duration(distance or 50) if distance else 120,
                request_data.get('notes', '')
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Delivery request created successfully",
                "request_id": request_id,
                "quoted_price": quoted_price,
                "estimated_distance_km": distance,
                "next_step": "Searching for available transporters"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def find_available_transporters(self, request_id: str) -> List[Dict]:
        """Find available transporters for a delivery request"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get delivery request details
            cur.execute('SELECT * FROM delivery_requests WHERE request_id = ?', (request_id,))
            request = cur.fetchone()
            
            if not request:
                return []
            
            # Find available transporters in the region
            query = '''
                SELECT * FROM transport_providers 
                WHERE status = 'available' 
                AND operating_region LIKE ? 
                AND vehicle_capacity >= ?
            '''
            
            # Add temperature requirement filter if needed
            if request['temperature_required']:
                query += " AND vehicle_type IN ('refrigerated_truck', 'temperature_controlled')"
            
            # Add budget constraint if provided
            if request['budget']:
                # Calculate estimated cost based on distance
                estimated_cost = self.estimate_delivery_price(
                    request['distance_km'] or 50,
                    request['quantity'],
                    request['commodity'],
                    request['temperature_required']
                )
                if estimated_cost <= request['budget'] * 1.2:  # Allow 20% flexibility
                    query += " AND minimum_charge <= ?"
                    params = (f"%{request['pickup_location'].split(',')[0]}%", 
                             request['quantity'], estimated_cost)
                else:
                    params = (f"%{request['pickup_location'].split(',')[0]}%", 
                             request['quantity'])
            else:
                params = (f"%{request['pickup_location'].split(',')[0]}%", 
                         request['quantity'])
            
            cur.execute(query, params)
            transporters = [dict(row) for row in cur.fetchall()]
            
            # Calculate distance and ETA for each transporter
            for transporter in transporters:
                if (transporter.get('gps_lat') and transporter.get('gps_lon') and
                    request.get('pickup_lat') and request.get('pickup_lon')):
                    distance_to_pickup = self.calculate_distance(
                        transporter['gps_lat'], transporter['gps_lon'],
                        request['pickup_lat'], request['pickup_lon']
                    )
                    transporter['distance_to_pickup_km'] = round(distance_to_pickup, 2)
                    transporter['eta_to_pickup_min'] = self.estimate_duration(distance_to_pickup)
                
                # Calculate total cost
                total_distance = (transporter.get('distance_to_pickup_km', 0) + 
                                (request['distance_km'] or 0))
                transporter['estimated_cost'] = self.calculate_transporter_cost(
                    transporter, total_distance, request['quantity']
                )
            
            # Sort by rating, then cost, then distance
            transporters.sort(key=lambda x: (
                -x['rating'],  # Higher rating first
                x.get('estimated_cost', float('inf')),  # Lower cost first
                x.get('distance_to_pickup_km', float('inf'))  # Closer first
            ))
            
            conn.close()
            return transporters[:10]  # Return top 10 matches
            
        except Exception as e:
            print(f"Error finding transporters: {e}")
            return []
    
    def assign_transporter(self, request_id: str, provider_id: str) -> Dict:
        """Assign a transporter to a delivery request"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get transporter details
            cur.execute('SELECT * FROM transport_providers WHERE provider_id = ?', (provider_id,))
            transporter = cur.fetchone()
            
            if not transporter:
                return {"success": False, "error": "Transporter not found"}
            
            # Get request details
            cur.execute('SELECT * FROM delivery_requests WHERE request_id = ?', (request_id,))
            request = cur.fetchone()
            
            if not request:
                return {"success": False, "error": "Delivery request not found"}
            
            # Check if request is still available
            if request['status'] != 'pending':
                return {"success": False, "error": f"Request already {request['status']}"}
            
            # Update delivery request
            cur.execute('''
                UPDATE delivery_requests 
                SET status = 'assigned', 
                    assigned_provider_id = ?,
                    assigned_provider_name = ?,
                    actual_price = ?,
                    updated_at = ?
                WHERE request_id = ?
            ''', (
                provider_id,
                transporter['name'],
                request['quoted_price'],
                datetime.now().isoformat(),
                request_id
            ))
            
            # Update transporter status
            cur.execute('''
                UPDATE transport_providers 
                SET status = 'busy',
                    last_active = ?
                WHERE provider_id = ?
            ''', (datetime.now().isoformat(), provider_id))
            
            # Create trip record
            trip_id = f"TRIP{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
            cur.execute('''
                INSERT INTO delivery_trips 
                (trip_id, request_id, provider_id, start_time, status_updates)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                trip_id,
                request_id,
                provider_id,
                datetime.now().isoformat(),
                json.dumps([{
                    'timestamp': datetime.now().isoformat(),
                    'status': 'assigned',
                    'location': transporter.get('current_location', 'Unknown'),
                    'notes': f"Assigned to {transporter['name']}"
                }])
            ))
            
            conn.commit()
            
            # Create cold chain monitoring if required
            if request['temperature_required']:
                self.setup_cold_chain_monitoring(request_id)
            
            # Send notifications (would integrate with SMS service)
            self.send_assignment_notification(request, transporter)
            
            conn.close()
            
            return {
                "success": True,
                "message": "Transporter assigned successfully",
                "trip_id": trip_id,
                "transporter": {
                    "name": transporter['name'],
                    "phone": transporter['phone'],
                    "vehicle": transporter['vehicle_type']
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== DELIVERY TRACKING ==========
    
    def update_delivery_status(self, trip_id: str, status: str, 
                               location: str = None, lat: float = None, 
                               lng: float = None, notes: str = "") -> Dict:
        """Update delivery status and location"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get trip details
            cur.execute('SELECT * FROM delivery_trips WHERE trip_id = ?', (trip_id,))
            trip = cur.fetchone()
            
            if not trip:
                return {"success": False, "error": "Trip not found"}
            
            # Get current status updates
            status_updates = json.loads(trip['status_updates'] or '[]')
            
            # Add new status update
            status_updates.append({
                'timestamp': datetime.now().isoformat(),
                'status': status,
                'location': location,
                'latitude': lat,
                'longitude': lng,
                'notes': notes
            })
            
            # Update trip status
            status_field = None
            if status == 'picked_up':
                status_field = 'pickup_time'
            elif status == 'delivered':
                status_field = 'delivery_time'
                # Also update delivery request
                cur.execute('''
                    SELECT request_id FROM delivery_trips WHERE trip_id = ?
                ''', (trip_id,))
                request_id = cur.fetchone()['request_id']
                
                cur.execute('''
                    UPDATE delivery_requests 
                    SET status = 'delivered', updated_at = ?
                    WHERE request_id = ?
                ''', (datetime.now().isoformat(), request_id))
                
                # Update transporter status back to available
                cur.execute('''
                    UPDATE transport_providers 
                    SET status = 'available',
                        total_trips = total_trips + 1,
                        last_active = ?
                    WHERE provider_id = ?
                ''', (datetime.now().isoformat(), trip['provider_id']))
            
            # Update trip record
            update_query = '''
                UPDATE delivery_trips 
                SET status_updates = ?
            '''
            params = [json.dumps(status_updates)]
            
            if status_field:
                update_query += f", {status_field} = ?"
                params.append(datetime.now().isoformat())
            
            update_query += " WHERE trip_id = ?"
            params.append(trip_id)
            
            cur.execute(update_query, params)
            
            # Update route coordinates if location provided
            if lat and lng:
                route_coords = json.loads(trip['route_coordinates'] or '[]')
                route_coords.append([lat, lng])
                cur.execute('''
                    UPDATE delivery_trips 
                    SET route_coordinates = ?
                    WHERE trip_id = ?
                ''', (json.dumps(route_coords), trip_id))
            
            conn.commit()
            conn.close()
            
            # Send status notification (would integrate with SMS)
            if status in ['picked_up', 'delivered', 'delayed']:
                self.send_status_notification(trip_id, status, notes)
            
            return {
                "success": True,
                "message": f"Status updated to '{status}'",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_delivery_tracking(self, trip_id: str) -> Dict:
        """Get real-time delivery tracking information"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get trip details with request info
            cur.execute('''
                SELECT dt.*, dr.*
                FROM delivery_trips dt
                JOIN delivery_requests dr ON dt.request_id = dr.request_id
                WHERE dt.trip_id = ?
            ''', (trip_id,))
            
            trip = cur.fetchone()
            
            if not trip:
                return {"error": "Trip not found"}
            
            # Parse status updates
            status_updates = json.loads(trip['status_updates'] or '[]')
            
            # Get cold chain data if available
            cold_chain_data = None
            cur.execute('SELECT * FROM cold_chain_monitoring WHERE request_id = ?', 
                       (trip['request_id'],))
            cold_chain = cur.fetchone()
            if cold_chain:
                cold_chain_data = {
                    'current_temperature': self.get_current_temperature(cold_chain),
                    'compliance_score': cold_chain['compliance_score'],
                    'violations': cold_chain['violation_count']
                }
            
            # Calculate progress
            progress = self.calculate_delivery_progress(trip)
            
            # Get transporter details
            cur.execute('SELECT * FROM transport_providers WHERE provider_id = ?', 
                       (trip['provider_id'],))
            transporter = cur.fetchone()
            
            conn.close()
            
            return {
                "trip_id": trip_id,
                "status": status_updates[-1]['status'] if status_updates else 'unknown',
                "current_location": status_updates[-1]['location'] if status_updates else 'Unknown',
                "progress": progress,
                "status_updates": status_updates,
                "cold_chain_monitoring": cold_chain_data,
                "transporter": dict(transporter) if transporter else None,
                "estimated_arrival": self.estimate_arrival_time(trip),
                "last_updated": status_updates[-1]['timestamp'] if status_updates else None
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # ========== COLD CHAIN MONITORING ==========
    
    def setup_cold_chain_monitoring(self, request_id: str) -> Dict:
        """Set up cold chain monitoring for a delivery"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # Get request details
            cur.execute('SELECT * FROM delivery_requests WHERE request_id = ?', (request_id,))
            request = cur.fetchone()
            
            if not request:
                return {"success": False, "error": "Request not found"}
            
            # Generate monitoring ID
            monitoring_id = f"CCM{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create monitoring record
            cur.execute('''
                INSERT INTO cold_chain_monitoring 
                (monitoring_id, request_id, device_id, monitoring_start,
                 min_temperature_violation, max_temperature_violation)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                monitoring_id,
                request_id,
                f"DEVICE{random.randint(1000, 9999)}",
                datetime.now().isoformat(),
                request['min_temperature'],
                request['max_temperature']
            ))
            
            # Start simulated temperature monitoring (in real app, would connect to IoT device)
            self.start_temperature_monitoring(monitoring_id, request_id)
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "monitoring_id": monitoring_id,
                "message": "Cold chain monitoring started"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def record_temperature_reading(self, monitoring_id: str, temperature: float, 
                                  humidity: float = None, lat: float = None, 
                                  lng: float = None) -> Dict:
        """Record temperature reading from IoT device"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get monitoring details
            cur.execute('SELECT * FROM cold_chain_monitoring WHERE monitoring_id = ?', 
                       (monitoring_id,))
            monitoring = cur.fetchone()
            
            if not monitoring:
                return {"success": False, "error": "Monitoring not found"}
            
            # Parse existing readings
            temp_readings = json.loads(monitoring['temperature_readings'] or '[]')
            humidity_readings = json.loads(monitoring['humidity_readings'] or '[]')
            location_updates = json.loads(monitoring['location_updates'] or '[]')
            
            # Add new readings
            timestamp = datetime.now().isoformat()
            temp_readings.append({
                'timestamp': timestamp,
                'temperature': round(temperature, 2)
            })
            
            if humidity is not None:
                humidity_readings.append({
                    'timestamp': timestamp,
                    'humidity': round(humidity, 2)
                })
            
            if lat and lng:
                location_updates.append({
                    'timestamp': timestamp,
                    'lat': lat,
                    'lng': lng
                })
            
            # Check for temperature violations
            violation_count = monitoring['violation_count']
            min_temp = monitoring['min_temperature_violation']
            max_temp = monitoring['max_temperature_violation']
            
            if min_temp and temperature < min_temp:
                violation_count += 1
                self.send_temperature_alert(monitoring_id, 'low', temperature, min_temp)
            elif max_temp and temperature > max_temp:
                violation_count += 1
                self.send_temperature_alert(monitoring_id, 'high', temperature, max_temp)
            
            # Calculate compliance score
            total_readings = len(temp_readings)
            compliance_score = ((total_readings - violation_count) / total_readings * 100 
                              if total_readings > 0 else 100)
            
            # Calculate average temperature
            avg_temp = sum(r['temperature'] for r in temp_readings) / len(temp_readings)
            
            # Update monitoring record
            cur.execute('''
                UPDATE cold_chain_monitoring 
                SET temperature_readings = ?,
                    humidity_readings = ?,
                    location_updates = ?,
                    violation_count = ?,
                    avg_temperature = ?,
                    compliance_score = ?
                WHERE monitoring_id = ?
            ''', (
                json.dumps(temp_readings[-100:]),  # Keep last 100 readings
                json.dumps(humidity_readings[-100:]),
                json.dumps(location_updates[-50:]),
                violation_count,
                round(avg_temp, 2),
                round(compliance_score, 2),
                monitoring_id
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Temperature recorded",
                "violation": violation_count > monitoring['violation_count'],
                "compliance_score": compliance_score
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== ROUTE OPTIMIZATION ==========
    
    def optimize_route(self, provider_id: str, deliveries: List[Dict]) -> Dict:
        """Optimize delivery route using simple algorithm"""
        try:
            if len(deliveries) < 2:
                return {"success": False, "error": "Need at least 2 deliveries to optimize"}
            
            # Get current location of transporter
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute('SELECT gps_lat, gps_lon FROM transport_providers WHERE provider_id = ?', 
                       (provider_id,))
            result = cur.fetchone()
            conn.close()
            
            if not result:
                current_lat, current_lon = -15.4167, 28.2833  # Default Lusaka
            else:
                current_lat, current_lon = result['gps_lat'], result['gps_lon']
            
            # Create locations list with current location as start
            locations = [{
                'id': 'start',
                'lat': current_lat,
                'lon': current_lon,
                'type': 'depot'
            }]
            
            for i, delivery in enumerate(deliveries):
                locations.append({
                    'id': delivery.get('request_id', f'delivery_{i}'),
                    'lat': delivery.get('pickup_lat', current_lat + random.uniform(-0.1, 0.1)),
                    'lon': delivery.get('pickup_lon', current_lon + random.uniform(-0.1, 0.1)),
                    'type': 'pickup',
                    'data': delivery
                })
            
            # Simple Nearest Neighbor Algorithm
            optimized_route = []
            unvisited = locations[1:]  # Exclude start
            current = locations[0]
            total_distance = 0
            
            while unvisited:
                # Find nearest unvisited location
                nearest = min(unvisited, 
                             key=lambda loc: self.calculate_distance(
                                 current['lat'], current['lon'], 
                                 loc['lat'], loc['lon']
                             ))
                
                # Calculate distance
                distance = self.calculate_distance(
                    current['lat'], current['lon'],
                    nearest['lat'], nearest['lon']
                )
                total_distance += distance
                
                # Add to route
                optimized_route.append({
                    'location_id': nearest['id'],
                    'lat': nearest['lat'],
                    'lon': nearest['lon'],
                    'type': nearest['type'],
                    'distance_from_previous': round(distance, 2),
                    'cumulative_distance': round(total_distance, 2)
                })
                
                # Update current and visited
                current = nearest
                unvisited.remove(nearest)
            
            # Add return to depot
            return_distance = self.calculate_distance(
                current['lat'], current['lon'],
                locations[0]['lat'], locations[0]['lon']
            )
            total_distance += return_distance
            
            # Calculate time estimate (assuming 40 km/h average)
            total_time_min = (total_distance / 40) * 60  # Convert hours to minutes
            
            # Save optimization result
            optimization_id = f"OPT{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.save_optimization_result(
                optimization_id, provider_id, optimized_route, 
                total_distance, total_time_min
            )
            
            return {
                "success": True,
                "optimization_id": optimization_id,
                "total_distance_km": round(total_distance, 2),
                "total_time_min": round(total_time_min),
                "route": optimized_route,
                "savings_estimate": self.calculate_savings_estimate(deliveries, total_distance)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== UTILITY FUNCTIONS ==========
    
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return self.earth_radius_km * c
    
    def estimate_delivery_price(self, distance_km: float, quantity_kg: float, 
                               commodity: str, temperature_required: bool) -> float:
        """Estimate delivery price based on multiple factors"""
        base_rate = 5.0  # ZMW per km
        
        # Adjust for commodity type
        commodity_factors = {
            'maize': 1.0,
            'tomatoes': 1.2,
            'vegetables': 1.3,
            'fruits': 1.4,
            'dairy': 1.5,
            'meat': 1.6,
            'general': 1.0
        }
        commodity_factor = commodity_factors.get(commodity.lower(), 1.0)
        
        # Adjust for temperature control
        temp_factor = 1.8 if temperature_required else 1.0
        
        # Adjust for quantity (economies of scale)
        quantity_factor = 1.0
        if quantity_kg > 1000:
            quantity_factor = 0.9
        elif quantity_kg > 5000:
            quantity_factor = 0.8
        
        # Calculate price
        price = (distance_km * base_rate * commodity_factor * 
                temp_factor * quantity_factor)
        
        # Add minimum charge
        min_charge = 100.0 if temperature_required else 50.0
        return max(price, min_charge)
    
    def estimate_duration(self, distance_km: float) -> int:
        """Estimate travel duration in minutes"""
        avg_speed_kmh = 40  # Average speed including stops
        buffer_factor = 1.3  # Buffer for traffic, loading, etc.
        
        duration_hours = distance_km / avg_speed_kmh * buffer_factor
        return int(duration_hours * 60)  # Convert to minutes
    
    def calculate_transporter_cost(self, transporter: Dict, distance_km: float, 
                                  quantity_kg: float) -> float:
        """Calculate cost for a specific transporter"""
        # Use per_km rate if available
        if transporter.get('per_km_rate'):
            cost = distance_km * transporter['per_km_rate']
        else:
            # Estimate based on vehicle type
            vehicle_rates = {
                'motorcycle': 4.0,
                'pickup': 6.0,
                'truck': 8.0,
                'refrigerated_truck': 12.0,
                'temperature_controlled': 15.0
            }
            rate = vehicle_rates.get(transporter['vehicle_type'], 8.0)
            cost = distance_km * rate
        
        # Ensure minimum charge
        if transporter.get('minimum_charge') and cost < transporter['minimum_charge']:
            cost = transporter['minimum_charge']
        
        return round(cost, 2)
    
    def calculate_delivery_progress(self, trip: Dict) -> Dict:
        """Calculate delivery progress percentage"""
        status_updates = json.loads(trip['status_updates'] or '[]')
        
        if not status_updates:
            return {"percentage": 0, "stage": "pending"}
        
        last_status = status_updates[-1]['status']
        
        # Define progress stages
        stages = {
            'pending': 0,
            'assigned': 10,
            'en_route_to_pickup': 30,
            'arrived_at_pickup': 40,
            'loading': 50,
            'picked_up': 60,
            'in_transit': 80,
            'arrived_at_delivery': 90,
            'delivered': 100
        }
        
        percentage = stages.get(last_status, 0)
        
        # If in transit, calculate based on route progress
        if last_status == 'in_transit' and trip.get('route_coordinates'):
            route_coords = json.loads(trip['route_coordinates'] or '[]')
            if len(route_coords) > 1:
                # Simplified: assume progress based on number of coordinates
                percentage = 60 + (len(route_coords) / 20 * 20)  # 60-80% range
        
        return {
            "percentage": min(100, percentage),
            "stage": last_status,
            "next_stage": self.get_next_stage(last_status)
        }
    
    def get_next_stage(self, current_stage: str) -> str:
        """Get next stage in delivery process"""
        stages = ['pending', 'assigned', 'en_route_to_pickup', 'arrived_at_pickup',
                 'loading', 'picked_up', 'in_transit', 'arrived_at_delivery', 'delivered']
        
        try:
            current_index = stages.index(current_stage)
            return stages[current_index + 1] if current_index + 1 < len(stages) else 'completed'
        except ValueError:
            return 'unknown'
    
    def estimate_arrival_time(self, trip: Dict) -> str:
        """Estimate arrival time based on current progress"""
        try:
            if not trip.get('pickup_time'):
                return "Not picked up yet"
            
            pickup_time = datetime.fromisoformat(trip['pickup_time'].replace('Z', '+00:00'))
            estimated_duration = trip.get('estimated_duration_min', 120)
            
            arrival_time = pickup_time + timedelta(minutes=estimated_duration)
            
            # Adjust based on current status
            status_updates = json.loads(trip['status_updates'] or '[]')
            if status_updates:
                last_update = datetime.fromisoformat(
                    status_updates[-1]['timestamp'].replace('Z', '+00:00')
                )
                time_since_pickup = (datetime.utcnow() - pickup_time).total_seconds() / 60
                
                if time_since_pickup > estimated_duration * 0.7:
                    # If more than 70% of estimated time has passed
                    remaining_percentage = 1 - (time_since_pickup / estimated_duration)
                    if remaining_percentage > 0:
                        new_estimate = time_since_pickup / (1 - remaining_percentage)
                        arrival_time = pickup_time + timedelta(minutes=new_estimate)
            
            return arrival_time.strftime("%Y-%m-%d %H:%M")
            
        except Exception:
            return "Unable to estimate"
    
    def calculate_savings_estimate(self, deliveries: List[Dict], 
                                  optimized_distance: float) -> Dict:
        """Calculate estimated savings from route optimization"""
        # Calculate unoptimized distance (straight sum)
        unoptimized_distance = sum(
            d.get('estimated_distance', 50) for d in deliveries
        )
        
        distance_saved = unoptimized_distance - optimized_distance
        fuel_saved = distance_saved * 0.12  # Assuming 12 liters per 100km
        time_saved = (distance_saved / 40) * 60  # 40 km/h average
        
        fuel_cost_per_liter = 25.0  # ZMW
        driver_cost_per_hour = 30.0  # ZMW
        
        monetary_savings = (fuel_saved * fuel_cost_per_liter + 
                           (time_saved / 60) * driver_cost_per_hour)
        
        return {
            "distance_saved_km": round(distance_saved, 2),
            "fuel_saved_liters": round(fuel_saved, 2),
            "time_saved_minutes": round(time_saved),
            "monetary_savings_zmw": round(monetary_savings, 2),
            "efficiency_gain": round((distance_saved / unoptimized_distance * 100), 2) 
            if unoptimized_distance > 0 else 0
        }
    
    def save_optimization_result(self, optimization_id: str, provider_id: str, 
                                route: List[Dict], total_distance: float, 
                                total_time: float) -> None:
        """Save route optimization result to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute('''
                INSERT INTO route_optimization 
                (optimization_id, provider_id, date, route_plan, 
                 total_distance, total_time_min, execution_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                optimization_id,
                provider_id,
                datetime.now().date().isoformat(),
                json.dumps(route),
                round(total_distance, 2),
                round(total_time),
                'planned'
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving optimization: {e}")
    
    def get_current_temperature(self, cold_chain: Dict) -> float:
        """Get current temperature from cold chain data"""
        try:
            readings = json.loads(cold_chain['temperature_readings'] or '[]')
            if readings:
                return readings[-1]['temperature']
        except:
            pass
        return None
    
    # ========== NOTIFICATION FUNCTIONS ==========
    
    def send_assignment_notification(self, request: Dict, transporter: Dict):
        """Send notification about assignment (stub for SMS integration)"""
        # In real implementation, integrate with your SMS service
        print(f"📱 Notification: Transporter {transporter['name']} assigned to request {request['request_id']}")
        
        # Farmer notification
        farmer_message = f"Your delivery request {request['request_id']} has been assigned to {transporter['name']} ({transporter['vehicle_type']}). Driver will contact you at {transporter['phone']}"
        
        # Transporter notification
        transporter_message = f"New delivery assignment: Pickup {request['commodity']} from {request['pickup_location']}. Farmer: {request['farmer_name']} ({request['farmer_phone']})"
        
        # Store notifications (would send via SMS in real app)
        self.store_notification(request['farmer_phone'], farmer_message)
        self.store_notification(transporter['phone'], transporter_message)
    
    def send_status_notification(self, trip_id: str, status: str, notes: str = ""):
        """Send status update notification (stub for SMS integration)"""
        print(f"📱 Status update: Trip {trip_id} - {status}: {notes}")
    
    def send_temperature_alert(self, monitoring_id: str, alert_type: str, 
                              current_temp: float, threshold: float):
        """Send temperature violation alert"""
        alert_message = f"🚨 COLD CHAIN ALERT: Temperature {alert_type.upper()} violation! Current: {current_temp}°C, Threshold: {threshold}°C"
        print(f"🌡️ {alert_message} (Monitoring: {monitoring_id})")
    
    def store_notification(self, phone: str, message: str):
        """Store notification for later sending (would integrate with SMS service)"""
        # In real app, add to SMS queue
        pass
    
    # ========== SIMULATION FUNCTIONS ==========
    
    def start_temperature_monitoring(self, monitoring_id: str, request_id: str):
        """Start simulated temperature monitoring (for demo)"""
        import threading
        
        def simulate_temperature():
            """Simulate temperature readings"""
            import time
            import random
            
            # Get temperature requirements
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute('SELECT min_temperature, max_temperature FROM delivery_requests WHERE request_id = ?', 
                       (request_id,))
            result = cur.fetchone()
            conn.close()
            
            min_temp = result['min_temperature'] if result and result['min_temperature'] else 2
            max_temp = result['max_temperature'] if result and result['max_temperature'] else 8
            
            # Simulate temperature readings every 5 minutes
            for _ in range(12):  # Simulate 1 hour
                time.sleep(5)  # 5 seconds for demo (would be 300 seconds in real)
                
                # Simulate temperature with occasional violations
                if random.random() < 0.1:  # 10% chance of violation
                    if random.random() < 0.5:
                        temp = min_temp - random.uniform(1, 3)  # Too cold
                    else:
                        temp = max_temp + random.uniform(1, 3)  # Too hot
                else:
                    temp = random.uniform(min_temp + 1, max_temp - 1)  # Normal
                
                # Record reading
                self.record_temperature_reading(
                    monitoring_id, 
                    temp,
                    humidity=random.uniform(60, 80),
                    lat=-15.4167 + random.uniform(-0.01, 0.01),
                    lng=28.2833 + random.uniform(-0.01, 0.01)
                )
        
        # Start simulation in background thread
        thread = threading.Thread(target=simulate_temperature, daemon=True)
        thread.start()

# ========== API ENDPOINTS FOR LOGISTICS ==========

def add_logistics_endpoints(app):
    """Add logistics endpoints to Flask app"""
    
    logistics = LogisticsModule()
    
    @app.route('/api/logistics/request', methods=['POST'])
    @token_required
    def create_delivery_request_api():
        """API endpoint to create delivery request"""
        data = request.json
        
        # Validate required fields
        required = ['farmer_id', 'pickup_location', 'delivery_location', 
                   'commodity', 'quantity', 'pickup_date']
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        result = logistics.create_delivery_request(data)
        return jsonify(result)
    
    @app.route('/api/logistics/transports/available', methods=['GET'])
    @token_required
    def get_available_transporters_api():
        """API endpoint to get available transporters for a request"""
        request_id = request.args.get('request_id')
        
        if not request_id:
            return jsonify({"error": "request_id parameter required"}), 400
        
        transporters = logistics.find_available_transporters(request_id)
        return jsonify({"transporters": transporters})
    
    @app.route('/api/logistics/assign', methods=['POST'])
    @token_required
    def assign_transporter_api():
        """API endpoint to assign transporter to request"""
        data = request.json
        
        if not data.get('request_id') or not data.get('provider_id'):
            return jsonify({"error": "request_id and provider_id required"}), 400
        
        result = logistics.assign_transporter(data['request_id'], data['provider_id'])
        return jsonify(result)
    
    @app.route('/api/logistics/track/<trip_id>', methods=['GET'])
    def track_delivery_api(trip_id):
        """API endpoint to track delivery"""
        result = logistics.get_delivery_tracking(trip_id)
        return jsonify(result)
    
    @app.route('/api/logistics/status/update', methods=['POST'])
    @token_required
    def update_delivery_status_api():
        """API endpoint to update delivery status"""
        data = request.json
        
        required = ['trip_id', 'status']
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        result = logistics.update_delivery_status(
            data['trip_id'],
            data['status'],
            data.get('location'),
            data.get('lat'),
            data.get('lng'),
            data.get('notes', '')
        )
        return jsonify(result)
    
    @app.route('/api/logistics/optimize', methods=['POST'])
    @token_required
    def optimize_route_api():
        """API endpoint to optimize delivery route"""
        data = request.json
        
        if not data.get('provider_id') or not data.get('deliveries'):
            return jsonify({"error": "provider_id and deliveries required"}), 400
        
        result = logistics.optimize_route(data['provider_id'], data['deliveries'])
        return jsonify(result)
    
    @app.route('/api/logistics/coldchain/reading', methods=['POST'])
    def record_temperature_api():
        """API endpoint to record temperature reading (for IoT devices)"""
        data = request.json
        
        required = ['monitoring_id', 'temperature']
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        result = logistics.record_temperature_reading(
            data['monitoring_id'],
            data['temperature'],
            data.get('humidity'),
            data.get('lat'),
            data.get('lng')
        )
        return jsonify(result)
    
    @app.route('/api/logistics/storage/facilities', methods=['GET'])
    def get_storage_facilities_api():
        """API endpoint to get storage facilities"""
        try:
            conn = sqlite3.connect('farm_market.db')
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            location = request.args.get('location', '')
            
            if location:
                cur.execute('''
                    SELECT * FROM storage_facilities 
                    WHERE location LIKE ? AND status = 'available'
                    ORDER BY rating DESC
                ''', (f'%{location}%',))
            else:
                cur.execute('''
                    SELECT * FROM storage_facilities 
                    WHERE status = 'available'
                    ORDER BY rating DESC
                ''')
            
            facilities = [dict(row) for row in cur.fetchall()]
            conn.close()
            
            return jsonify({"facilities": facilities})
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/logistics/provider/register', methods=['POST'])
    def register_transport_provider_api():
        """API endpoint to register transport provider"""
        data = request.json
        
        required = ['name', 'phone', 'vehicle_type', 'vehicle_capacity']
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        try:
            conn = sqlite3.connect('farm_market.db')
            cur = conn.cursor()
            
            provider_id = f"TP{datetime.now().strftime('%Y%m%d')}{random.randint(100, 999)}"
            
            cur.execute('''
                INSERT INTO transport_providers 
                (provider_id, name, owner_name, phone, email, vehicle_type, 
                 vehicle_capacity, vehicle_registration, operating_region, 
                 current_location, gps_lat, gps_lon, hourly_rate, per_km_rate, 
                 minimum_charge, verified, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                provider_id,
                data['name'],
                data.get('owner_name', ''),
                data['phone'],
                data.get('email', ''),
                data['vehicle_type'],
                data['vehicle_capacity'],
                data.get('vehicle_registration', ''),
                data.get('operating_region', ''),
                data.get('current_location', ''),
                data.get('gps_lat'),
                data.get('gps_lon'),
                data.get('hourly_rate', 0),
                data.get('per_km_rate', 0),
                data.get('minimum_charge', 0),
                data.get('verified', 0),
                data.get('notes', '')
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                "success": True,
                "message": "Transport provider registered successfully",
                "provider_id": provider_id
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/logistics/stats', methods=['GET'])
    @admin_required
    def logistics_stats_api():
        """API endpoint to get logistics statistics"""
        try:
            conn = sqlite3.connect('farm_market.db')
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Count requests by status
            cur.execute('''
                SELECT status, COUNT(*) as count 
                FROM delivery_requests 
                GROUP BY status
            ''')
            requests_by_status = {row['status']: row['count'] for row in cur.fetchall()}
            
            # Count transporters by status
            cur.execute('''
                SELECT status, COUNT(*) as count 
                FROM transport_providers 
                GROUP BY status
            ''')
            transporters_by_status = {row['status']: row['count'] for row in cur.fetchall()}
            
            # Recent deliveries
            cur.execute('''
                SELECT dr.request_id, dr.commodity, dr.quantity, dr.pickup_location, 
                       dr.delivery_location, dr.status, dt.trip_id,
                       tp.name as transporter_name
                FROM delivery_requests dr
                LEFT JOIN delivery_trips dt ON dr.request_id = dt.request_id
                LEFT JOIN transport_providers tp ON dr.assigned_provider_id = tp.provider_id
                ORDER BY dr.created_at DESC 
                LIMIT 10
            ''')
            recent_deliveries = [dict(row) for row in cur.fetchall()]
            
            # Revenue statistics
            cur.execute('''
                SELECT 
                    SUM(CASE WHEN payment_status = 'completed' THEN amount ELSE 0 END) as total_revenue,
                    SUM(CASE WHEN payment_status = 'pending' THEN amount ELSE 0 END) as pending_revenue,
                    COUNT(*) as total_transactions
                FROM logistics_transactions
            ''')
            revenue_stats = dict(cur.fetchone())
            
            conn.close()
            
            return jsonify({
                "requests": {
                    "total": sum(requests_by_status.values()),
                    "by_status": requests_by_status
                },
                "transporters": {
                    "total": sum(transporters_by_status.values()),
                    "by_status": transporters_by_status
                },
                "revenue": revenue_stats,
                "recent_deliveries": recent_deliveries
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return app

# ========== TESTING ==========

if __name__ == "__main__":
    # Test the logistics module
    logistics = LogisticsModule()
    
    # Create test request
    test_request = {
        "farmer_id": "user_001",
        "farmer_name": "John Farmer",
        "farmer_phone": "+260971234567",
        "pickup_location": "Lusaka Farm, Chongwe Road",
        "pickup_lat": -15.4167,
        "pickup_lon": 28.2833,
        "delivery_location": "Lusaka Central Market",
        "delivery_lat": -15.4167,
        "delivery_lon": 28.2833,
        "commodity": "Tomatoes",
        "quantity": 1000,
        "pickup_date": datetime.now().date().isoformat(),
        "temperature_required": True,
        "min_temperature": 5,
        "max_temperature": 10,
        "budget": 500
    }
    
    result = logistics.create_delivery_request(test_request)
    print("Create Request:", result)
    
    if result["success"]:
        request_id = result["request_id"]
        transporters = logistics.find_available_transporters(request_id)
        print(f"\nAvailable Transporters: {len(transporters)} found")
        
        if transporters:
            # Assign first available transporter
            assignment = logistics.assign_transporter(request_id, transporters[0]["provider_id"])
            print("\nAssignment:", assignment)