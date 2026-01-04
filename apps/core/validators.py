"""
File upload validators using magic bytes for MIME type detection.

Prevents malicious file uploads by validating actual file content,
not just the file extension which can be easily spoofed.
"""
import magic
from django.core.exceptions import ValidationError


# Allowed image MIME types and their valid extensions
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': {'.jpg', '.jpeg'},
    'image/png': {'.png'},
    'image/gif': {'.gif'},
    'image/webp': {'.webp'},
}

# Allowed receipt types (images + PDF)
ALLOWED_RECEIPT_TYPES = {
    **ALLOWED_IMAGE_TYPES,
    'application/pdf': {'.pdf'},
}

# Maximum file sizes
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_RECEIPT_SIZE = 10 * 1024 * 1024  # 10MB


def validate_file_type(file, allowed_types: dict, max_size: int = None) -> None:
    """
    Validate file by MIME type using magic bytes.

    This provides much stronger security than extension-only validation
    because it checks the actual file content signature.

    Args:
        file: Uploaded file object (from request.FILES)
        allowed_types: Dict mapping MIME types to sets of allowed extensions
        max_size: Optional maximum file size in bytes

    Raises:
        ValidationError: If file type is invalid or size exceeds limit
    """
    # Validate file size first
    if max_size and file.size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValidationError(f'File too large. Maximum size is {max_mb:.0f}MB.')

    # Read file header to detect MIME type
    file_header = file.read(2048)
    file.seek(0)  # Reset file pointer for later use

    try:
        detected_mime = magic.from_buffer(file_header, mime=True)
    except Exception as e:
        raise ValidationError(f'Could not determine file type: {e}')

    # Check if MIME type is allowed
    if detected_mime not in allowed_types:
        allowed_list = ', '.join(sorted(allowed_types.keys()))
        raise ValidationError(
            f'Invalid file type: {detected_mime}. '
            f'Allowed types: {allowed_list}'
        )

    # Validate extension matches detected MIME type
    if hasattr(file, 'name') and file.name:
        ext = ''
        if '.' in file.name:
            ext = '.' + file.name.rsplit('.', 1)[-1].lower()

        valid_extensions = allowed_types.get(detected_mime, set())
        if ext and ext not in valid_extensions:
            raise ValidationError(
                f'File extension "{ext}" does not match detected type "{detected_mime}". '
                f'Expected extensions: {", ".join(sorted(valid_extensions))}'
            )


def validate_image_file(file) -> None:
    """
    Validate an image file upload.

    Args:
        file: Uploaded file object

    Raises:
        ValidationError: If not a valid image or exceeds size limit
    """
    validate_file_type(file, ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE)


def validate_receipt_file(file) -> None:
    """
    Validate a receipt file upload (image or PDF).

    Args:
        file: Uploaded file object

    Raises:
        ValidationError: If not a valid receipt type or exceeds size limit
    """
    validate_file_type(file, ALLOWED_RECEIPT_TYPES, MAX_RECEIPT_SIZE)
