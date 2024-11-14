from dotenv import load_dotenv
import os
import uuid

class Utilities:
    def __init__(self) -> None:
        pass

    def Load_Env():
        """
        Load environment variables from .env file
        Returns:
            bool: True if environment variables were loaded successfully
        """
        try:
            # Load environment variables from .env file
            load_dotenv()
            return True
        except Exception as e:
            print(f"Error loading environment variables: {e}")
            return False
        
    def get_env_variable(key: str, default: str = None) -> str:
        """
        Get environment variable value
        Args:
            key: Environment variable key
            default: Default value if key not found
        Returns:
            str: Environment variable value
        """
        return os.getenv(key, default)
    
    
    def generate_uuid() -> str:
        """
        Generate a unique UUID
        Returns:
            str: UUID string
        """
        return str(uuid.uuid4())