# Location-Based Incident Filtering

## Overview
Implemented location-based filtering that shows incidents to users based on their city/area. This ensures users only see relevant incidents from their local region, making the system more practical and focused.

## How It Works

### 1. User Location Storage
- Each user's city, state, country, latitude, and longitude are stored in the database
- Location data is loaded into the user session during login
- Session variables: `user_city`, `user_latitude`, `user_longitude`, `user_role`

### 2. Incident Filtering
**Backend Filtering (`frontend/app.py` - `/api/incidents`)**
- Admins see **ALL** incidents from all locations
- Operators and Viewers see only incidents from their **assigned city**
- SQL query filters by city: `WHERE status != 'RESOLVED' AND (city = ? OR city IS NULL)`

### 3. Map Centering
**Frontend (`frontend/templates/dashboard.html`)**
- Map automatically centers on user's city coordinates (zoom level 12)
- Falls back to Malaysia center view if no coordinates are available
- Jinja2 template:
  ```jinja
  {% if user_latitude and user_longitude %}
  var map = L.map('map').setView([{{ user_latitude }}, {{ user_longitude }}], 12);
  {% else %}
  var map = L.map('map').setView([4.2105, 101.9758], 7);
  {% endif %}
  ```

### 4. Location Badge
- Active Incidents card shows location badge
- Displays user's city (for operators/viewers)
- Shows "All Locations" badge for admins with globe icon

## Updated Database

### User Locations
| Username | Role | City | Latitude | Longitude |
|----------|------|------|----------|-----------|
| admin | admin | - | - | - |
| traffic_authority | admin | - | - | - |
| police | operator | Penang | 5.4164 | 100.3327 |
| ambulance | operator | Johor Bahru | 1.4927 | 103.7414 |
| hospital | operator | Ipoh | 4.5975 | 101.0901 |
| resident1 | viewer | Kuching | 1.5535 | 110.3593 |
| resident2 | viewer | Kuala Lumpur | 3.1390 | 101.6869 |
| policy_makers | viewer | Penang | 5.4164 | 100.3327 |
| researchers | viewer | Johor Bahru | 1.4927 | 103.7414 |
| user1 | viewer | Ipoh | 4.5975 | 101.0901 |

### Accident Locations
- All 391 accidents updated with city information
- Cities distributed across: Kuala Lumpur, Penang, Johor Bahru, Ipoh, Melaka, Kuching
- Each accident assigned based on GPS coordinates or randomly for testing

## User Experience

### For Admins
- ✅ See all incidents from all cities
- ✅ Map shows Malaysia-wide view (zoom 7)
- ✅ Green "All Locations" badge displayed

### For Operators (police, ambulance, hospital)
- ✅ See only incidents from their assigned city
- ✅ Map centers on their city (zoom 12)
- ✅ Blue city badge shows their location

### For Viewers (residents, researchers, policy makers)
- ✅ See only incidents from their neighborhood
- ✅ Map centers on their city for relevant view
- ✅ Blue city badge shows filtering is active

## Benefits

1. **Relevance**: Users see only incidents that matter to them
2. **Performance**: Reduced data load per user
3. **Focus**: Emergency responders see incidents in their coverage area
4. **Scalability**: System can handle nationwide deployment with local filtering
5. **Privacy**: Users only see information relevant to their area

## Testing

To test the feature:
1. **Login as admin** → See all incidents from all cities
2. **Login as police (Penang)** → See only Penang incidents
3. **Login as resident2 (Kuala Lumpur)** → See only KL incidents
4. **Login as ambulance (Johor Bahru)** → See only JB incidents

Map will automatically center on each user's city.

## Files Modified

1. **frontend/app.py**
   - Session storage for user location (lines 213-216)
   - City-based incident filtering (lines 451-470)
   - Dashboard route passes location data (lines 271-282)

2. **frontend/templates/dashboard.html**
   - Location badge in Active Incidents header
   - Map centering based on user coordinates
   - Admin/user role differentiation

3. **database/update_user_locations.py**
   - Script to assign cities to users
   - Coordinates for 6 major Malaysian cities

4. **database/update_accident_locations.py**
   - Script to assign cities to existing accidents
   - SQLite-based updates for 391 records

## Future Enhancements

- [ ] Radius-based filtering (show incidents within X km)
- [ ] Multi-city access for regional admins
- [ ] City selector dropdown for admins to filter view
- [ ] Automatic city detection from IP geolocation
- [ ] Coverage area visualization on map
