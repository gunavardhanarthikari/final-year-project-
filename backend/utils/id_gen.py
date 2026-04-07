"""
ID Generator Utility for TrueFace AI
Generates sequential IDs for Users and Faces
"""
import re

def generate_readable_id(role, current_count):
    """
    Generates a readable ID based on role or type.
    AD: Administrator
    MG: Manager (High-end)
    VW: Viewer (Low-end)
    FC: Face Image
    """
    prefixes = {
        'ADMIN': 'AD',
        'MANAGER': 'MG',
        'VIEWER': 'VW',
        'FACE': 'FC'
    }
    
    prefix = prefixes.get(role, 'XX')
    new_number = current_count + 1
    return f"{prefix}{new_number:03d}"

def get_next_id(model, role=None):
    """
    Queries the database for the next sequential ID
    """
    from database import db
    
    # For Users, we filter by role prefix if needed, 
    # but the user requested explicit prefixes based on role.
    # So we count total users of that role.
    if role == 'FACE':
        count = model.query.count()
        return generate_readable_id('FACE', count)
    else:
        # Count users of this specific role to get the next number
        from database.models import User
        count = User.query.filter_by(role=role).count()
        return generate_readable_id(role, count)
