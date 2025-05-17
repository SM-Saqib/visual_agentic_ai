from fastapi import FastAPI, File, UploadFile
from fastapi import Request, Depends
from fastapi.responses import JSONResponse
import os
from pathlib import Path
import shutil
from fastapi import APIRouter

from backend.models import PresentationURL

from backend.database.base import get_db

db_connection = get_db()

router = APIRouter()

UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload/")
async def upload_file(
    request: Request,
    presentation_type: str,
    file: UploadFile = File(...),
    db=Depends(get_db),
):
    """
    Upload a file and return its URL.
    """
    try:
        # Save the file to the uploads directory
        file_location = UPLOAD_DIR / file.filename
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Generate the full URL for the uploaded file
        base_url = str(request.base_url).rstrip("/")  # Get the base URL of the app
        print("Base URL:", base_url)

        file_url = f"{base_url}/api/ppt/media/{file.filename}"

        # now, lets save the file to the database

        file_db = PresentationURL(
            url=file_url,
            url_type=presentation_type,
        )

        # Save the file URL to the database
        db.add(file_db)
        db.commit()
        db.refresh(file_db)

        return JSONResponse(
            content={
                "filename": file.filename,
                "url": file_url,
            }
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


from fastapi.responses import FileResponse


@router.get("/media/{filename}")
async def get_uploaded_file(filename: str, db=Depends(get_db)):
    """
    Retrieve the exact file that was uploaded by its filename.
    """
    try:
        # # Query the database for the file
        # file_record = (
        #     db.query(PresentationURL)
        #     .filter(PresentationURL.url.contains(filename))
        #     .first()
        # )

        # if not file_record:
        #     return JSONResponse(content={"error": "File not found"}, status_code=404)

        # Construct the file path
        file_path = UPLOAD_DIR / filename

        # Check if the file exists in the uploads directory
        if not file_path.exists():
            return JSONResponse(
                content={"error": "File not found on disk"}, status_code=404
            )

        # Serve the file
        return FileResponse(
            file_path, media_type="application/octet-stream", filename=filename
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
