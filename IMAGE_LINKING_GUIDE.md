# 🖼️ Image Upload & Report Linking Guide

## Overview
Your CarbonIQ API now supports multiple ways to link images to waste reports:

1. **Two-step process**: Upload image first, then create report with image URL
2. **Single-step process**: Create report with image in one request  
3. **Add image later**: Upload image to existing report

---

## 🚀 **Method 1: Two-Step Process (Recommended)**

### Step 1: Upload Image
```bash
POST /reports/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

Form Data:
- file: [image file]
```

**Response:**
```json
{
  "filename": "1723567623_user_photo.jpg",
  "url": "/static/images/1723567623_user_photo.jpg",
  "size": 1024000,
  "uploaded_by": "user@example.com",
  "uploaded_at": "2025-08-13T17:00:00.000000"
}
```

### Step 2: Create Report with Image URL
```bash
POST /reports/
Authorization: Bearer <token>
Content-Type: application/json

{
  "student_id": "student123",
  "waste_type": "recyclable_plastic",
  "location": {
    "type": "Point",
    "coordinates": [-74.006, 40.7128]
  },
  "image_url": "/static/images/1723567623_user_photo.jpg",
  "safe": true,
  "urban_area": true
}
```

---

## 🎯 **Method 2: Single-Step Process**

### Create Report with Image Upload
```bash
POST /reports/with-image
Authorization: Bearer <token>
Content-Type: multipart/form-data

Form Data:
- student_id: "student123"
- waste_type: "recyclable_plastic"
- longitude: -74.006
- latitude: 40.7128
- safe: true
- urban_area: true
- file: [image file]
```

**Response:**
```json
{
  "id": "report_id_here",
  "student_id": "student123",
  "waste_type": "recyclable_plastic",
  "image_url": "/static/images/1723567623_user_photo.jpg",
  "location": {
    "type": "Point",
    "coordinates": [-74.006, 40.7128]
  },
  "status": "new",
  "priority": 0,
  "created_by": "user@example.com"
}
```

---

## 🔧 **Method 3: Add Image to Existing Report**

### Upload Image to Existing Report
```bash
PATCH /reports/{report_id}/image
Authorization: Bearer <token>
Content-Type: multipart/form-data

Form Data:
- file: [image file]
```

**Response:**
```json
{
  "message": "Image added to report successfully",
  "report_id": "report_id_here",
  "image_url": "/static/images/1723567623_user_photo.jpg",
  "filename": "1723567623_user_photo.jpg"
}
```

---

## 📱 **Postman Testing Examples**

### Test 1: Upload Image First
1. **Method**: POST
2. **URL**: `http://localhost:8000/reports/upload`
3. **Headers**: `Authorization: Bearer <your_token>`
4. **Body**: 
   - Type: form-data
   - Key: `file` (Type: File)
   - Value: Select an image file

### Test 2: Create Report with Image URL
1. **Method**: POST
2. **URL**: `http://localhost:8000/reports/`
3. **Headers**: 
   - `Authorization: Bearer <your_token>`
   - `Content-Type: application/json`
4. **Body (JSON)**:
```json
{
  "student_id": "student123",
  "waste_type": "recyclable_plastic",
  "location": {
    "type": "Point",
    "coordinates": [-74.006, 40.7128]
  },
  "image_url": "/static/images/your_uploaded_image.jpg",
  "safe": true,
  "urban_area": true
}
```

### Test 3: Single-Step Report + Image
1. **Method**: POST
2. **URL**: `http://localhost:8000/reports/with-image`
3. **Headers**: `Authorization: Bearer <your_token>`
4. **Body**: 
   - Type: form-data
   - Add these fields:
     - `student_id`: student123
     - `waste_type`: recyclable_plastic
     - `longitude`: -74.006
     - `latitude`: 40.7128
     - `safe`: true
     - `urban_area`: true
     - `file`: [Select image file]

---

## 🔍 **View Reports with Images**

### Get All Reports
```bash
GET /reports/
```

### Get Specific Report
```bash
GET /reports/{report_id}
```

### Filter Reports
```bash
GET /reports/?waste_type=recyclable_plastic&status=new
```

---

## 🖼️ **Image File Support**

### Supported Formats:
- ✅ **JPEG** (.jpg, .jpeg)
- ✅ **PNG** (.png)
- ✅ **WebP** (.webp)
- ✅ **GIF** (.gif)

### File Naming:
Images are automatically renamed to: `{timestamp}_{user}_{original_name}`

Example: `1723567623_testuser_waste_photo.jpg`

---

## 📂 **File Storage**

### Local Development:
- Images stored in: `backend/storage/images/`
- Accessible via: `http://localhost:8000/static/images/{filename}`

### Production Recommendations:
- Use cloud storage (AWS S3, Google Cloud Storage)
- Set up CDN for faster image delivery
- Implement image compression/resizing

---

## 🔒 **Security Features**

### Authentication:
- ✅ All upload endpoints require valid JWT token
- ✅ Users can only modify their own reports (unless admin/staff)

### File Validation:
- ✅ File type validation (only images allowed)
- ✅ Filename sanitization
- ✅ User identification in filename

### Permissions:
- **Students**: Can upload images to their own reports
- **Staff/Admin**: Can upload images to any report

---

## 💡 **Best Practices**

### For Frontend Developers:
1. **Always upload image first**, then create report
2. **Handle upload progress** for better UX
3. **Validate file size** before upload (recommend < 5MB)
4. **Show image preview** after upload
5. **Provide fallback** if image upload fails

### For Mobile Apps:
1. **Use single-step endpoint** `/reports/with-image` for simplicity
2. **Compress images** before upload
3. **Handle offline scenarios** (save to upload later)

### Error Handling:
```javascript
try {
  const uploadResponse = await uploadImage(file);
  const reportResponse = await createReport({
    ...reportData,
    image_url: uploadResponse.url
  });
} catch (error) {
  // Handle upload or report creation failure
  console.error('Failed to create report with image:', error);
}
```

---

## 🎯 **Complete Workflow Example**

```javascript
// Complete workflow for creating report with image
async function createReportWithImage(reportData, imageFile) {
  try {
    // Step 1: Upload image
    const formData = new FormData();
    formData.append('file', imageFile);
    
    const uploadResponse = await fetch('/reports/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });
    
    const uploadResult = await uploadResponse.json();
    
    // Step 2: Create report with image URL
    const reportResponse = await fetch('/reports/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ...reportData,
        image_url: uploadResult.url
      })
    });
    
    const report = await reportResponse.json();
    console.log('Report created with image:', report);
    
    return report;
  } catch (error) {
    console.error('Failed to create report with image:', error);
    throw error;
  }
}
```

Your image linking functionality is now complete! 🎉
