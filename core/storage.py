import os
from cloudinary_storage.storage import MediaCloudinaryStorage

RAW_EXTENSIONS = {
    'doc', 'docx', 'txt', 'csv', 'xls', 'xlsx',
    'zip', 'rar', 'tar', 'gz', 'json', 'xml'
}
VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm', 'mkv'}


class SmartMediaCloudinaryStorage(MediaCloudinaryStorage):
    """
    Cloudinary media storage that dynamically determines resource_type
    ('raw', 'video', or 'image') based on the file extension.
    By default, MediaCloudinaryStorage uploads everything as 'image',
    which causes Cloudinary to reject Word documents (.doc/.docx) with 
    'Invalid image file' errors.
    """
    def _get_resource_type(self, name):
        if not name:
            return self.RESOURCE_TYPE
        ext = name.split('.')[-1].lower() if '.' in name else ''
        if ext in RAW_EXTENSIONS:
            return 'raw'
        if ext in VIDEO_EXTENSIONS:
            return 'video'
        return 'image'
