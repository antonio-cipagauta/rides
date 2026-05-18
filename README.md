# Rides API

A Django REST Framework API for managing rides, drivers, riders, and ride events. Built with token-based authentication, role-based permissions, proximity-based search, and paginated responses.

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/antonio-cipagauta/rides.git && cd rides
uv sync
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
DJANGO_SECRET_KEY="your-secret-key"
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1"
DATABASE_URL="postgres://user:pass@127.0.0.1:5432/rides_db"
```

> Leave `DATABASE_URL` blank to default to SQLite.

### 3. Run Migrations

```bash
uv run python manage.py migrate
```

### 4. Create an Admin User

```bash
uv run python manage.py shell
```

```python
from rides.utils import create_admin_user, get_or_create_auth_token

user = create_admin_user(
    email="admin@example.com",
    first_name="Admin",
    last_name="User",
)
token = get_or_create_auth_token("admin@example.com")
print(token.key)  # Use this token for API requests
```

### 5. Seed Sample Data (Optional)

```bash
uv run python seed_rides.py
```

Creates 10 riders, 10 drivers, 50 rides (centered around Boston), and associated ride events.

### 6. Run the Server

```bash
uv run python manage.py runserver
```

## Authentication

All endpoints require a valid token in the `Authorization` header. Only users with the `admin` role are permitted access.

```
Authorization: Token <your-token>
```

## API Endpoints

Base URL: `/api/`

| Resource | Endpoint | Methods |
| Users | `/api/users/` | GET, POST, PUT, PATCH, DELETE |
| Rides | `/api/rides/` | GET, POST, PUT, PATCH, DELETE |
| Ride Events | `/api/events/` | GET, POST, PUT, PATCH, DELETE |

All list endpoints are paginated (default: 10 items per page, max: 100).

### Pagination

| Parameter | Description | Default |
| `page` | Page number | `1` |
| `page_size` | Results per page | `10` |

```
GET /api/rides/?page=2&page_size=25
```

### Filtering Rides

| Parameter | Description | Example |
| `status` | Exact match on ride status | `?status=en-route` |
| `rider_email` | Case-insensitive exact match on rider email | `?rider_email=rider1@example.com` |

### Proximity Search

Pass `ref_lat` and `ref_lng` to find rides near a location. Results are bounded to a ~25km box and sorted by distance (closest first).

```
GET /api/rides/?ref_lat=42.3557&ref_lng=-71.0656
```

When no coordinates are provided, rides are sorted by `pickup_time` (most recent first).

### Ordering

Use the `ordering` query parameter on the rides endpoint:

```
GET /api/rides/?ordering=pickup_time
GET /api/rides/?ordering=-pickup_time
```

## Data Models

### User

Extending Django's `AbstractUser` with:

| Field | Type | Notes |
| `id_user` | AutoField | Primary key |
| `role` | CharField | `admin`, `rider`, or `driver` |
| `email` | EmailField | Unique |
| `phone_number` | CharField | Optional |

Extending `AbstractUser` for authentication purposes.

### Ride

| Field | Type | Notes |
| `id_ride` | AutoField | Primary key |
| `status` | CharField | `en-route`, `pickup`, or `dropoff` (indexed) |
| `id_rider` | ForeignKey → User | Nullable |
| `id_driver` | ForeignKey → User | Nullable |
| `pickup_latitude` | FloatField | Indexed |
| `pickup_longitude` | FloatField | Indexed |
| `dropoff_latitude` | FloatField | |
| `dropoff_longitude` | FloatField | |
| `pickup_time` | DateTimeField | Indexed |

A composite index on `(pickup_latitude, pickup_longitude)` optimizes bounding-box queries.

### RideEvent

| Field | Type | Notes |
| `id_ride_event` | AutoField | Primary key |
| `id_ride` | ForeignKey → Ride | Nullable |
| `description` | CharField | Max 100 chars |
| `created_at` | DateTimeField | Auto-set, indexed |

## Performance Notes

- **`select_related`** on `id_rider` and `id_driver` eliminates N+1 queries when serializing rides
- **`prefetch_related`** with a filtered `Prefetch` loads only the last 24 hours of ride events in a single query
- **Database indexes** on `status`, `pickup_time`, `created_at`, and a composite index on `(pickup_latitude, pickup_longitude)` for fast filtering and proximity search
- **Bounding-box pre-filter** narrows the candidate set before computing distances, keeping the sort efficient
- **Debug query logger** in `RideViewSet.dispatch()` is guarded behind `DEBUG` — zero overhead in production

## Development

### Linting

```bash
uv run ruff check .
uv run ruff format .
```

Ruff is configured in `pyproject.toml` with Django-specific rules enabled.

Main challenge was optimizing the queries to reduce the number of database queries and improve performance. This required using a logger to count number of queries and see which queries were being executed, this made debugging and improving them easy.

The design decision to extend AbstractUser was for authentication purposes, to restrict access only to admin users using token-based authentication.

### BONUS SQL

```sql
SELECT
    DATE_TRUNC('month', pickup.created_at)         AS month,
    u.first_name || ' ' || u.last_name             AS driver,
    COUNT(*)                                       AS trip_count
FROM rides_ride r
JOIN rides_rideevent pickup
    ON pickup.id_ride_id = r.id_ride
    AND pickup.description = 'Status changed to pickup'
JOIN rides_rideevent dropoff
    ON dropoff.id_ride_id = r.id_ride
    AND dropoff.description = 'Status changed to dropoff'
JOIN rides_user u
    ON u.id_user = r.id_driver_id
WHERE dropoff.created_at - pickup.created_at > INTERVAL '1 hour'
GROUP BY month, driver
ORDER BY month, trip_count DESC;
```
