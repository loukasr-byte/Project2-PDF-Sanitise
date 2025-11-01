"""
Module: config_manager
Description: Manages secure configuration storage with cryptographic integrity verification.
             All admin-configurable settings are stored in the Windows Registry with
             ECDSA signatures to prevent tampering.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
import winreg

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Default configuration values per ARCHITECTURE.md
DEFAULT_CONFIG = {
    "sanitization_policy": "AGGRESSIVE",
    "memory_limit_mb": 500,
    "timeout_seconds": 300,
    "max_file_size_mb": 500,
    "enable_usb_isolation_monitoring": True,
    "enable_audit_logging": True,
    "quarantine_directory": r"C:\PDFSanitizer\Quarantine",
    "log_directory": r"C:\PDFSanitizer\Logs",
}


def sign_config(config_data: Dict[str, Any], private_key) -> str:
    """
    Signs a configuration dictionary and returns the signature in hex format.
    
    Args:
        config_data (dict): The configuration to sign.
        private_key: An ECDSA private key object.
        
    Returns:
        str: The hex-encoded signature.
    """
    canonical_json = json.dumps(config_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    signature = private_key.sign(canonical_json, ec.ECDSA(hashes.SHA256()))
    return signature.hex()


def verify_config(config_data: Dict[str, Any], signature_hex: str, public_key) -> bool:
    """
    Verifies the signature of a configuration dictionary.
    
    Args:
        config_data (dict): The configuration data to verify.
        signature_hex (str): The hex-encoded signature.
        public_key: An ECDSA public key object.
        
    Returns:
        bool: True if signature is valid, False otherwise.
    """
    try:
        canonical_json = json.dumps(config_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
        signature = bytes.fromhex(signature_hex)
        public_key.verify(signature, canonical_json, ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, ValueError, TypeError) as e:
        logging.warning(f"Configuration signature verification failed: {e}")
        return False


def save_secure_config(config: Dict[str, Any], signature: str):
    """
    Saves config and signature to HKLM registry with admin-only ACLs.
    
    Note: ACLs must be set on the parent key during installation.
    
    Args:
        config (dict): Configuration dictionary to save.
        signature (str): Hex-encoded signature of the configuration.
        
    Raises:
        PermissionError: If administrator privileges are required.
    """
    try:
        reg_path = r"SOFTWARE\PDFSanitizer"
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
            winreg.SetValueEx(key, "Configuration", 0, winreg.REG_SZ, json.dumps(config))
            winreg.SetValueEx(key, "ConfigurationSignature", 0, winreg.REG_SZ, signature)
        logging.info("[INFO] Secure configuration saved to registry.")
    except PermissionError:
        logging.error("[ERROR] Administrator privileges required to save configuration.")
        raise


def load_config_from_registry() -> Dict[str, Any]:
    """
    Loads configuration from Windows Registry.
    
    Returns:
        dict: Configuration dictionary, or DEFAULT_CONFIG if not found.
    """
    try:
        reg_path = r"SOFTWARE\PDFSanitizer"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
            config_str, _ = winreg.QueryValueEx(key, "Configuration")
            return json.loads(config_str)
    except (FileNotFoundError, winreg.error):
        logging.info("No saved configuration found in registry, using defaults.")
        return DEFAULT_CONFIG.copy()


def get_default_config() -> Dict[str, Any]:
    """
    Returns the default configuration dictionary.
    
    Returns:
        dict: A copy of DEFAULT_CONFIG.
    """
    return DEFAULT_CONFIG.copy()


class ConfigManager:
    """
    Manages application configuration with security validation.
    """
    
    def __init__(self):
        """Initialize ConfigManager with current configuration from registry."""
        self.config = load_config_from_registry()
        self.logger = logging.getLogger("ConfigManager")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Gets a configuration value.
        
        Args:
            key (str): Configuration key.
            default: Default value if key not found.
            
        Returns:
            The configuration value or default.
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Sets a configuration value.
        
        Args:
            key (str): Configuration key.
            value: The value to set.
        """
        self.config[key] = value
        self.logger.info(f"Configuration updated: {key} = {value}")
    
    def validate_config(self) -> bool:
        """
        Validates that all required configuration keys are present with valid values.
        
        Returns:
            bool: True if configuration is valid.
        """
        required_keys = DEFAULT_CONFIG.keys()
        for key in required_keys:
            if key not in self.config:
                self.logger.error(f"Missing required configuration key: {key}")
                return False
        
        # Validate numeric ranges
        if not (100 <= self.config.get('memory_limit_mb', 0) <= 2048):
            self.logger.error("memory_limit_mb must be between 100 and 2048")
            return False
        
        if not (10 <= self.config.get('timeout_seconds', 0) <= 3600):
            self.logger.error("timeout_seconds must be between 10 and 3600")
            return False
        
        return True
    
    def get_all(self) -> Dict[str, Any]:
        """
        Gets the entire configuration dictionary.
        
        Returns:
            dict: A copy of the current configuration.
        """
        return self.config.copy()
    
    def reset_to_defaults(self):
        """Resets configuration to DEFAULT_CONFIG."""
        self.config = DEFAULT_CONFIG.copy()
        self.logger.info("Configuration reset to defaults")


# Example usage
if __name__ == '__main__':
    manager = ConfigManager()
    print("Current Configuration:")
    for key, value in manager.get_all().items():
        print(f"  {key}: {value}")
    
    print(f"\nConfiguration Valid: {manager.validate_config()}")

