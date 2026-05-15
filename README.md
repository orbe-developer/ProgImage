# ProgImage

A FastAPI-based REST API for image storage, retrieval, and transformation. Accepts image uploads, persists them to PostgreSQL, and exposes a suite of image processing operations — compression, rotation, filtering, and masking.

**Stack:** Python · FastAPI · PostgreSQL · Pillow · Peewee ORM

---

## Features

- Upload and retrieve images (JPG, PNG)
- Compress and resize images to target dimensions
- Rotate images by arbitrary angle
- Generate thumbnails
- Apply 11 image filters (blur, sharpen, edge detection, emboss, contour, and more)
- Image masking with composite operations and drawn masks (ellipse, blurred ellipse)

---

## API Endpoints

Base URL: `http://localhost:8000/api/v1`

### Images
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/images` | Upload image (jpg, jpeg, png) |
| `GET` | `/images/{image_id}` | Retrieve image by ID |

### Processing
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/images/processing/compress_image` | Resize to given dimensions |
| `POST` | `/images/processing/rotate_image` | Rotate by angle |
| `POST` | `/images/processing/thumbnail_image` | Generate thumbnail |

### Filtering
| Method | Path |
|--------|------|
| `POST` | `/images/filtering/filter_blur` |
| `POST` | `/images/filtering/filter_contour` |
| `POST` | `/images/filtering/filter_detail` |
| `POST` | `/images/filtering/filter_edge_enhance` |
| `POST` | `/images/filtering/filter_edge_enhance_more` |
| `POST` | `/images/filtering/filter_emboss` |
| `POST` | `/images/filtering/filter_find_edges` |
| `POST` | `/images/filtering/filter_smooth` |
| `POST` | `/images/filtering/filter_smooth_more` |
| `POST` | `/images/filtering/filter_sharpen` |
| `POST` | `/images/filtering/filter_gaussian_blur` |
| `POST` | `/images/filtering/filter_unsharp_mask` |

### Masking
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/images/masking/mask_image` | Blend two images with opacity mask |
| `POST` | `/images/masking/mask_image_drawing_circle` | Mask with ellipse cutout |
| `POST` | `/images/masking/mask_image_drawing_blur_circle` | Mask with blurred ellipse |
| `POST` | `/images/masking/mask_image_existing_image` | Mask using a third image |

Interactive docs available at `http://localhost:8000/docs` when running locally.

---

## Running Locally

### Prerequisites
- Python 3.x
- PostgreSQL running on `localhost:5432`
- Database `heycar_db` created

### Setup

```bash
pip install fastapi python-multipart uvicorn peewee pillow
uvicorn app.main:app --reload
```

On startup the application connects to PostgreSQL and creates the `images` table if it does not exist.

---

## Project Structure

```
ProgImage/
└── app/
    ├── main.py                 ← FastAPI app and lifecycle hooks
    ├── database.py             ← Peewee ORM and Image model
    └── routers/
        ├── images.py           ← Upload and retrieval
        ├── image_processing.py
        ├── image_filtering.py
        ├── image_masking.py
        ├── wrappers.py         ← Validation decorators
        └── util.py             ← Helper functions
```
