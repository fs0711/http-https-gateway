"""
Test script to verify wsgi.py imports correctly
"""

def test_wsgi_import():
    """Test that wsgi.py can be imported without errors"""
    try:
        import wsgi
        print("✓ wsgi.py imported successfully")
        
        # Check if app object exists
        if hasattr(wsgi, 'app'):
            print("✓ app object found in wsgi module")
        else:
            print("✗ app object not found in wsgi module")
            return False
        
        # Check if app is a Flask instance
        from flask import Flask
        if isinstance(wsgi.app, Flask):
            print("✓ app is a valid Flask instance")
        else:
            print("✗ app is not a Flask instance")
            return False
        
        print("\n✓ All WSGI tests passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import wsgi.py: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during WSGI test: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("WSGI Configuration Test")
    print("=" * 60)
    test_wsgi_import()
